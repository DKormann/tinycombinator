
import subprocess, ctypes, os, hashlib, threading
import time
import sys
from typing import Callable, Dict

from tinycombinator.run import reduce
from tinycombinator.ast import IC, Tag
from tinycombinator.helpers import BACKEND, DEBUG, TIMEIT, hide_dups

def to_c_data(node: IC) -> list[int]:
  """Serialize a IC graph to a flat int array for passing to C"""
  ctx : Dict[IC, int] = {}
  nodes = []
  taken = {}

  def take(owner: IC, owned: IC):
    if owned in taken: raise ValueError(f"IC {owned} is already taken by {taken[owned]}")
    taken[owned] = owner
  
  def visit(n: IC):
    if n is None or n in ctx: return
    ctx[n] = len(nodes) + 1  # 1-indexed, 0 is NULL
    nodes.append(n)
    visit(n.s0)
    visit(n.s1)

    if DEBUG:
      match n.tag:
        case Tag.Lam: take(n, n.s0)
        case Tag.App | Tag.Sup:
          take(n, n.s0)
          take(n, n.s1)

  visit(node)

  for i, n in enumerate(nodes):
    if n.tag == Tag.App and n.s1 is None:
        raise ValueError(f"Invalid App at index {i}: s1 (argument) is None. App must have both function (s0) and argument (s1). s0={n.s0}")
    
  data = [len(nodes)]
  for i, n in enumerate(nodes):
    data.extend([n.tag.value-1, n.label or 0, ctx.get(n.s0, 0), ctx.get(n.s1, 0)])
  
  return data

def from_c_data(res:ctypes.POINTER(ctypes.c_int))->IC:


  l = res[0]
  if l == -1: raise RuntimeError("Segmentation fault occurred in C code")
  
  nodes = [None] + [IC(None) for _ in range(l)]

  for i in range(l):
    if DEBUG>1: print(res[i * 4 + 1])
    nodes[i + 1].tag = list(Tag.__members__.values())[res[i * 4 + 1]]
    nodes[i + 1].label = res[i * 4 + 2]
    nodes[i + 1].s0 = nodes[res[i * 4 + 3]]
    nodes[i + 1].s1 = nodes[res[i * 4 + 4]]

  def refcount(node:IC)->int: return sum((n.s0 == node) + (n.s1 == node) for n in nodes[1:])

  for node in nodes[1:]:
    if node.tag == Tag.Lam and refcount(node.s1) < 2: node.s1 = None

  return nodes[1]

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
    if  f.read().strip() != c_hash: compile_c()


_local = threading.local()




def get_lib():
  if not hasattr(_local, 'lib'):
    _local.lib = ctypes.CDLL(so_path)
    def go(name, inp, out):
      getattr(_local.lib, name).argtypes = inp
      getattr(_local.lib, name).restype = out
    go("get_node_count", [ctypes.c_void_p], ctypes.c_int)
    go("load", [ctypes.POINTER(ctypes.c_int)], ctypes.c_void_p)
    go("unload", [ctypes.c_void_p], ctypes.POINTER(ctypes.c_int))
    go("set_debug", [ctypes.c_int], None)
    go("run", [ctypes.c_int, ctypes.c_void_p], ctypes.c_int)
    _local.lib.set_debug(DEBUG.get())
  
  _local.lib.set_debug(DEBUG.get())

  return _local.lib

def load_term_c(term: IC) -> ctypes.c_void_p: return get_lib().load((ctypes.c_int * len(to_c_data(term)))(*to_c_data(term)))

def unload_term_c(runtime) -> IC: return from_c_data(get_lib().unload(runtime))

DEFAULT_FUEL = 1<<30

def run(runtime, steps:int = DEFAULT_FUEL):
  return get_lib().run(steps, runtime)

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
    print(f"Final result:")
    with hide_dups(True): print(term)
  return term


def execute(node:IC, *args, **kwargs)->Callable[[IC, int, int], IC]:
  if BACKEND == "c": return run_term_c(node, *args, **kwargs)
  if BACKEND == "py":

    return reduce(node.copy())
  raise ValueError(f"Invalid backend: {BACKEND}")
