import ctypes
import hashlib
import os
from pathlib import Path
from re import I

from tinycombinator.helpers import DEBUG, debug

from tinycombinator.nodes import AUX1, AUX2, MAIN, Node, Port, Tag, wire
from tinycombinator.term import Term


current_dir = Path(__file__).parent

c_path = current_dir / "main.c"
lib_path = current_dir / "tmp"
os.makedirs(lib_path.parent, exist_ok=True)


def get_lib():

  c_code = c_path.read_text()
  c_hash = hashlib.sha256(c_code.encode()).hexdigest()

  if (not (lib_path / "hash").exists()) or (c_hash != (lib_path/"hash").read_text()):
    debug("compiling ... ")
    os.system(f"clang -shared -o {lib_path/ 'main.so'} {c_path}")
    (lib_path/"hash").write_text(c_hash)

  import threading

  local = threading.local()
  if not hasattr(local, "lib"):
    local.lib = ctypes.CDLL(lib_path / "main.so")
    def fun(name, ins, outs):
      getattr(local.lib, name).argtypes = ins
      getattr(local.lib, name).restype = outs

    fun("new_runtime", [], ctypes.c_void_p)
    fun("new_term", [ctypes.c_int, ctypes.c_int, ctypes.c_void_p], ctypes.c_int)
    fun("set_root", [ctypes.c_int, ctypes.c_void_p], None)
    fun("get_root", [ctypes.c_void_p], ctypes.c_int)
    fun("set_port", [ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_void_p], None)

    fun("get_tag", [ctypes.c_int, ctypes.c_void_p], ctypes.c_int)
    fun("get_label", [ctypes.c_int, ctypes.c_void_p], ctypes.c_int)
    fun("get_port_target", [ctypes.c_int, ctypes.c_int, ctypes.c_void_p], ctypes.c_int)
    fun("get_port_side", [ctypes.c_int, ctypes.c_int, ctypes.c_void_p], ctypes.c_int)

    fun("set_dup_aux", [ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_void_p], None)
    

  return local.lib

DEBUG.set(1)
lib = get_lib()


def sides(tag:Tag, need_term:bool): return [i for i in range(3) if tag.negative_polarity(i) == need_term]

def serialize_term(term:Term, lib:ctypes.CDLL):
  rt = lib.new_runtime()
  cache = {}

  root = (Port(Node(Tag.ROOT), MAIN))


  wire(root, term.port)

  for node in term.port.node.walk(): cache[node] = lib.new_term(node.tag.value, node.label, rt)

  lib.set_root(cache[root.node], rt)


  for node in term.port.node.walk():

    def port_side_to_c(port:Port, need_term: bool)->int:
      try: return sides(port.node.tag, need_term).index(port.side)
      except ValueError: raise ValueError(f"illegal port: {port}, {need_term}")

    def c_connect(node:Node, side, target:Port, need_term: bool=True):
      lib.set_port(cache[node],side,cache[target.node],port_side_to_c(target, need_term),rt,)

    match node.tag:

      case Tag.App:
        c_connect(node, 0, node.con[MAIN])
        c_connect(node, 1, node.con[AUX1])
      case Tag.Lam:
        c_connect(node, 0, node.con[AUX1], False) # var creates a term
        c_connect(node, 1, node.con[AUX2])
      case Tag.Sup:
        c_connect(node, 0, node.con[AUX1])
        c_connect(node, 1, node.con[AUX2])
      
      case Tag.Dup:
        c_connect(node, 0, node.con[MAIN])
        a,b = node.con[AUX1:AUX2+1]
        lib.set_dup_aux(cache[node],
        cache[a.node], port_side_to_c(a, False),
        cache[b.node], port_side_to_c(b, False), rt)

      
      case Tag.Null | Tag.ERA: pass
      case Tag.ROOT: c_connect(node, 0, node.con[MAIN])

      case _: raise ValueError(f"illegal node: {node}")


  return rt


def deserialize_term(rt:ctypes.c_void_p, lib:ctypes.CDLL):

  root = lib.get_root(rt)
  cache = {}

  def go(loc:int)->Node:
    if loc in cache: return cache[loc]

    node = Node(Tag(lib.get_tag(loc, rt)), lib.get_label(loc, rt))

    cache[loc] = node

    def connect(side:int, c_side:int):
      tar = go(lib.get_port_target(loc, c_side, rt))
      oside = sides(tar.tag, not node.tag.negative_polarity(side))[lib.get_port_side(loc, c_side, rt)]
      wire((node, side), (tar, oside))

    match node.tag:
      case Tag.ROOT:
        connect( MAIN, 0)
      case Tag.App:
        connect(MAIN, 0)
        connect(AUX1, 1)
      case Tag.Sup | Tag.Lam:
        connect(AUX1, 0)
        connect(AUX2, 1)
      case Tag.Dup:
        connect(MAIN, 0)
        """ you could get the other port from the aux ports but need to reverse xored data"""

    return node

  node = go(root)

  return Term(Port(node, MAIN).other())





def round_trip(term:Term):
  s = str(term)
  r = serialize_term(term, lib)
  d = deserialize_term(r, lib)
  assert str(d) == s



t = Term(lambda x, y: x)
t2 = Term(lambda x, y: y)


round_trip(Term.sup(t, t2))

t0 = Term(lambda x:x)

round_trip(t0)

ds = t0.dups()

round_trip(Term(lambda x: ds[0](ds[1])))


print("OK")

