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

  return local.lib

DEBUG.set(1)
lib = get_lib()


def sides(tag:Tag, need_term:bool): return [i for i in range(3) if tag.negative_polarity(i) == need_term]

def serialize_term(term:Term, lib:ctypes.CDLL):
  rt = lib.new_runtime()
  cache = {}

  for node in term.port.node.walk(): cache[node] = lib.new_term(node.tag.value, node.label, rt)

  for node in term.port.node.walk():

    def port_side_to_c(port:Port, need_term: bool)->int:
      try: return sides(port.node.tag, need_term).index(port.side)
      except ValueError: raise ValueError(f"illegal port: {port}, {need_term}")

    def c_connect(node, side, target:Port, need_term: bool=True):
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
        raise RuntimeError("not implemented")
      
      case Tag.Null | Tag.ERA: pass

      case _: raise ValueError(f"illegal node: {node}")


  return rt


def deserialize_term(rt:ctypes.c_void_p, lib:ctypes.CDLL):

  root = lib.get_root(rt)
  cache = {}

  def port_side_from_c(tag:Tag, cside:int, need_term:bool = True):
    return sides(tag, need_term)[cside]

  def go(loc:int):
    if loc in cache: return cache[loc]
    tag = Tag(lib.get_tag(loc, rt))
    node = Node(tag, lib.get_label(loc, rt))

    cache[loc] = node

    match tag:
      case Tag.App:
        pass
      
      case Tag.Lam:
        vr = go(lib.get_port_target(loc, 0, rt))
        side = port_side_from_c(vr.tag, lib.get_port_side(loc, 0, rt), False)
        wire(Port(node, AUX1), Port(vr, side))

        bod = go(lib.get_port_target(loc, 1, rt))
        side = port_side_from_c(bod.tag, lib.get_port_side(loc, 1, rt), True)
        wire(Port(node, AUX2), Port(bod,side))

    return node

  node = go(root)

  return Term(Port(node, MAIN))


t = Term(lambda x, y: x)
r = serialize_term(t, lib)
d = deserialize_term(r, lib)
print(d)


