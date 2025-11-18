import ctypes
import hashlib
import os
from pathlib import Path
from tinycombinator.helpers import DEBUG, debug
from tinycombinator.nodes import PN, Node, Port, Tag, wire, MathOps
from tinycombinator.term import Term


current_dir = Path(__file__).parent
c_path = current_dir / "main.c"
lib_path = current_dir / "tmp"

os.makedirs(lib_path.parent, exist_ok=True)

CPtr = ctypes.c_void_p
Cint = ctypes.c_int
PORT = ctypes.c_int32

def make_port(loc: int, side: int) -> int: return (loc << 1) | side
def get_loc(port: int) -> int: return port >> 1
def get_side(port: int) -> int: return port & 1


def encoded_ports(tag:Tag):
  match tag:
    case Tag.App: return [PN.MAIN, PN.AUX1]
    case Tag.Lam | Tag.Sup: return [PN.AUX1, PN.AUX2]
    case Tag.Dup: return [PN.MAIN, PN.AUX1, PN.AUX2]
    case Tag.ROOT | Tag.ERA: return [PN.MAIN]
  return []

def neg_ports(tag:Tag): return [i for i in PN if tag.negative_polarity(i)]

side = int
num = int

def CCall(name:str, argtypes: list[type], restype: type, *args):

  if len(argtypes) != len(args):
    print(f"ERROR CLANGCALL: {name} {argtypes} {args}")
    exit(256)
  import threading
  local = threading.local()
  if not hasattr(local, "lib"):
    c_code = c_path.read_text()
    c_hash = hashlib.sha256(c_code.encode()).hexdigest()
    if (not (lib_path / "hash").exists()) or (c_hash != (lib_path/"hash").read_text()):
      debug("compiling ... ")
      if os.system(f"clang -shared -o {lib_path/ 'main.so'} {c_path}"):
        print("\x1b[31mCLANG ERROR\x1b[0m")
        exit(256) 
      (lib_path/"hash").write_text(c_hash)

    local.lib = ctypes.CDLL(lib_path / "main.so")
  
  local.lib.set_debug.argtypes = [Cint]
  local.lib.set_debug(DEBUG.get())

  fun = getattr(local.lib, name)
  fun.argtypes = argtypes
  fun.restype = restype
  res = fun(*args)
  return res

def serialize_node(root:Node)->CPtr:

  rt = CCall("new_runtime", [], CPtr)
  cache = {}
  for node in root.walk():
    port = CCall("new_node", [Cint, Cint, CPtr], Cint, node.tag.value, node.label, rt)
    cache[node] = get_loc(port)
  
  CCall("set_root", [Cint, CPtr], None, cache[root], rt)

  for node in root.walk():
    def c_connect(side:int):
      portn = encoded_ports(node.tag)[side]
      other = Port(node, portn).other()
      neg = node.tag.negative_polarity(portn)
      options = (encoded_ports if neg else neg_ports)(other.tag)
      cside = options.index(other.number)
      CCall("set_port", [PORT, PORT, CPtr], None, make_port(cache[node], side), make_port(cache[other.node], cside), rt)
      assert CCall("get_port", [PORT, CPtr], PORT, make_port(cache[node], side), rt) == make_port(cache[other.node], cside)

    match node.tag:
      case Tag.Dup:
        c_connect(0)
        ps = []
        for i in [PN.AUX1, PN.AUX2]:
          o = node.con[i]
          oside = encoded_ports(o.tag).index(o.number)
          ps.append(make_port(cache[o.node], oside))
        CCall("set_dup_aux", [PORT, PORT, PORT, CPtr], None, make_port(cache[node], 0), ps[0], ps[1], rt)
      case Tag.Prim:
        CCall("set_port", [PORT, PORT, CPtr], None, make_port(cache[node], 0),
        make_port(node.value, 0) if isinstance(node.value, int) else make_port(node.value.value, 1), rt)
      case _:
        for i in range(len(encoded_ports(node.tag))): c_connect(i)


  return rt


def deserialize_term(rt:CPtr):
  cache = {}
  def go(port:PORT)->Node:
    loc = get_loc(port)
    if loc in cache: return cache[loc]

    tag = CCall("get_tag", [PORT, CPtr], Cint, port, rt)

    label= CCall("get_label", [PORT, CPtr], Cint, port, rt)
    node = Node(Tag(tag), label)
    cache[loc] = node

    def connect(side:int, pn:PN):

      my_c_port = CCall("get_port", [PORT, CPtr], PORT, make_port(loc, side), rt)
      oside = get_side(my_c_port)
      o = go(my_c_port)
      c_port = (encoded_ports if node.tag.negative_polarity(pn) else neg_ports)(o.tag)[oside]
      wire((node, pn),(o, c_port))

    match node.tag:
      case Tag.Dup:
        connect(0, PN.MAIN)
        """TODO?"""
      case Tag.Prim: raise ValueError("Prim not supported")
      case Tag.ERA: pass
      case _:
        for i in enumerate(encoded_ports(node.tag)): connect(*i)
    return node

  
  return go(CCall("get_root", [CPtr], Cint, rt))


def run(root:Node, steps:int):
  r = serialize_node(root)
  CCall("run", [CPtr, Cint], Cint, r, steps)
  d = deserialize_term(r).con[0]
  wire((root, 0), d)




