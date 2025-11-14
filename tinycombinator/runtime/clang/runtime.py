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


class CPort(ctypes.Structure):
  loc: int
  side: int
  _fields_ = [("loc", ctypes.c_int32), ("side", ctypes.c_int32)]


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

  fun = getattr(local.lib, name)
  fun.argtypes = argtypes
  fun.restype = restype
  return fun(*args)  

    





def serialize_node(root:Node)->CPtr:
  rt = CCall("new_runtime", [], CPtr)
  cache = {}
  for node in root.walk(): cache[node] = CCall("new_node", [Cint, Cint, CPtr], Cint, node.tag.value, node.label, rt)
  
  CCall("set_root", [Cint, CPtr], None, cache[root], rt)

  for root in root.walk():

    def c_connect(side:int):

      portn = encoded_ports(root.tag)[side]
      o = Port(root, portn).other()
      neg = root.tag.negative_polarity(portn)
      cside = (encoded_ports if neg else neg_ports)(o.tag).index(o.number)

      # debug(f"\n\nCONNECT: {root} {side=} {portn} {neg=}")
      # debug(f"OTHER: {o.node} {cside=} {o.number} {cside}")


      CCall("set_port", [CPort, CPort, CPtr], None, CPort(cache[root], side), CPort(cache[o.node], cside), rt)

    match root.tag:
      case Tag.Dup:
        c_connect(0)
        ps = []
        for i in [PN.AUX1, PN.AUX2]:
          o = root.con[i].other()
          oside = encoded_ports(o.tag).index(o.number)
          ps.append(CPort(cache[root], oside))
        CCall("set_dup_aux", [Cint, CPort, CPort, CPtr], None, cache[root], *ps, rt)
      case Tag.Prim:
        CCall("set_port", [CPort, CPort, CPtr], None, CPort(cache[root], 0),
        CPort(root.value,0) if isinstance(root.value, int) else CPort(root.value.value,1), rt)
      case _:
        for i in range(len(encoded_ports(root.tag))): c_connect(i)

  return rt


def deserialize_term(rt:CPtr):
  cache = {}
  def go(loc:int)->Node:
    if loc in cache: return cache[loc]
    node = Node(Tag(CCall("get_tag", [Cint, CPtr], Cint, loc, rt)), CCall("get_label", [Cint, CPtr], Cint, loc, rt))
    cache[loc] = node

    def connect(side:int, pn:PN):
      port: CPort = CCall("get_port", [CPort, CPtr], CPort, CPort(loc, side), rt)
      o = go(port.loc)
      c_port = (encoded_ports if node.tag.negative_polarity(pn) else neg_ports)(o.tag)[port.side]
      wire((node, pn),(o, c_port))

    match node.tag:
      case Tag.Dup:
        connect(0, PN.MAIN)
        """TODO"""
      case Tag.Prim:
        dat = CCall("get_port", [CPort, CPtr], CPort, CPort(loc, 0), rt)
        node.value = MathOps(dat.loc) if dat.side else dat.loc
      case _:
        for i in enumerate(encoded_ports(node.tag)): connect(*i)
    return node
  return go(CCall("get_root", [CPtr], Cint, rt))


def run(root:Node, steps:int):

  r = serialize_node(root)
  CCall("run", [CPtr, Cint], Cint, r, steps)
  wire((root, 0), deserialize_term(r).con[0])



