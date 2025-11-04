
import subprocess, ctypes, os, hashlib, threading
import time
import sys
from typing import Callable, Dict

from tinycombinator.run import reduce
from tinycombinator.ast import IC, Tag
from tinycombinator.helpers import BACKEND, DEBUG, TIMEIT, hide_dups


tmp_path = os.path.join( os.path.dirname(__file__), "../.tmp")

os.makedirs(tmp_path, exist_ok=True)

so_path = os.path.join(tmp_path, "main.so")
c_cache_path = os.path.join(tmp_path, "c_hash")
main_path = os.path.join(os.path.dirname(__file__), "main.c")


with open(main_path, "rb") as f: c_hash = hashlib.md5(f.read()).hexdigest()

def compile_c():
  with open(c_cache_path, "w") as f: f.write(c_hash)
  print("Compiling...")
  os.makedirs(tmp_path, exist_ok=True)
  subprocess.check_call(["clang", "-shared", "-O2", "-fPIC", main_path, "-o", so_path])

if not os.path.exists(c_cache_path): compile_c()
else:
  with open(c_cache_path, "r") as f:
    if f.read().strip() != c_hash: compile_c()

_local = threading.local()

def get_lib():
  if not hasattr(_local, 'lib'):
    _local.lib = ctypes.CDLL(so_path)
    def go(name, inp, out):
      getattr(_local.lib, name).argtypes = inp
      getattr(_local.lib, name).restype = out
    go("get_root", [ctypes.c_void_p], ctypes.c_void_p)
    go("get_tag", [ctypes.c_void_p], ctypes.c_int)
    go("get_label", [ctypes.c_void_p], ctypes.c_int)
    go("get_s0", [ctypes.c_void_p], ctypes.c_void_p)
    go("get_s1", [ctypes.c_void_p], ctypes.c_void_p)
    go("get_node_count", [ctypes.c_void_p], ctypes.c_int)
    go("new_runtime", [], ctypes.c_void_p)
    go("empty_node", [ctypes.c_int, ctypes.c_int, ctypes.c_void_p], ctypes.c_void_p)
    go("set_auxs", [ctypes.c_void_p, ctypes.c_void_p, ctypes.c_void_p], None)
    go("set_debug", [ctypes.c_int], None)
    go("run", [ctypes.c_int, ctypes.c_void_p], ctypes.c_int)
    _local.lib.set_debug(DEBUG.get())
  
  _local.lib.set_debug(DEBUG.get())

  return _local.lib

def load_term_c(term: IC)->ctypes.c_void_p:
  nodes = dict[IC, ctypes.c_void_p]()
  runtime = get_lib().new_runtime()
  def visit(node: IC):
    if node is None or node in nodes: return
    nodes[node] = get_lib().empty_node(node.tag.value - 1, node.label if node.label is not None else 0, runtime)
    visit(node.s0)
    visit(node.s1)
  
  visit(term)

  for node in nodes: get_lib().set_auxs( nodes[node], nodes[node.s0] if node.s0 is not None else 0, nodes[node.s1] if node.s1 is not None else 0,)
  return runtime


all_tags = list(Tag.__members__.values())

def unload_term_c(runtime)->IC:
  lib = get_lib()
  root = lib.get_root(runtime)
  nodes: Dict[ctypes.c_void_p, IC] = {}
  nodes[None] = None
  taken = set()

  def visit(node: ctypes.c_void_p):
    if node not in nodes:
      nodes[node] = IC(all_tags[lib.get_tag(node)], label = lib.get_label(node))
      nodes[node].s0 = visit(lib.get_s0(node))
      nodes[node].s1 = visit(lib.get_s1(node))
    else: taken.add(node)
    return nodes[node]
  
  visit(root)
  
  for node in nodes:
    ic = nodes[node]
    if node is not None and ic.tag == Tag.Var and node not in taken:
      ic.s0.s1 = None
  return nodes[root]


DEFAULT_FUEL = 1<<30
def run(runtime, steps:int = DEFAULT_FUEL): return get_lib().run(steps, runtime)

def get_node_count_c() -> int: return get_lib().get_node_count()

def run_term_c(term:IC, maxsteps: int = DEFAULT_FUEL, runs = DEFAULT_FUEL) -> IC:

  t = 0

  if DEBUG: print(term)
  for batch in range(runs):
    runtime = load_term_c(term)
    st = time.time_ns()
    steps = run(runtime, int(maxsteps))
    t += time.time_ns() - st
    term = unload_term_c(runtime)
    sys.stdout.flush()
    if DEBUG: print(term)
    if steps < maxsteps: break
  if TIMEIT:
    total_steps = batch * maxsteps + steps
    print(f"\n{total_steps} steps: {t/1e9} seconds {(total_steps)/(t+1e-9)*1e3:.3f} Mips")
  if DEBUG:
    with hide_dups(True): print(term)
  return term


def execute(node:IC, *args, **kwargs)->Callable[[IC, int, int], IC]:
  if BACKEND == "c": return run_term_c(node, *args, **kwargs)
  if BACKEND == "py": return reduce(node.copy())
  raise ValueError(f"Invalid backend: {BACKEND}")
