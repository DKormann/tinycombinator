import ctypes
import hashlib
import os
from pathlib import Path
from re import I
from tinycombinator.helpers import DEBUG, debug
from tinycombinator.nodes import AUX1, AUX2, MAIN, Node, Port, Tag, wire, MathOps
from tinycombinator.term import Term


current_dir = Path(__file__).parent

c_path = current_dir / "main.c"
lib_path = current_dir / "tmp"
os.makedirs(lib_path.parent, exist_ok=True)

class CPort(ctypes.Structure):
  loc: int
  side: int
  _fields_ = [("loc", ctypes.c_int32), ("side", ctypes.c_int32)]


def encoded_ports(tag:Tag):
  match tag:
    case Tag.App: return [MAIN, AUX1]
    case Tag.Lam | Tag.Dup | Tag.Sup: return [AUX1, AUX2]
  return [MAIN]

def term_ports(tag:Tag): return [i for i in range(3) if tag.negative_polarity(i)]
def is_subst(tag:Tag, num:int): return (tag == Tag.Lam and num == AUX1) or (tag == Tag.Dup and num != MAIN)

side = int
num = int

def to_c_port(port:Port) -> side:
  tag = port.node.tag
  num = port.number
  otag = port.node.con[num].node.tag
  onum = port.node.con[num].number
  opts = (encoded_ports if is_subst(tag, num) else term_ports)(otag)
  return opts.index(onum)

def from_c_port(tag:Tag, num:int, otag:Tag, side:int) -> num: return (encoded_ports if is_subst(tag, num) else term_ports)(otag)[side]
    




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
    fun("run", [ctypes.c_void_p], ctypes.c_int)
    fun("new_node", [ctypes.c_int, ctypes.c_int, ctypes.c_void_p], ctypes.c_int)
    fun("set_root", [ctypes.c_int, ctypes.c_void_p], None)
    fun("get_root", [ctypes.c_void_p], ctypes.c_int)
    fun("set_port", [CPort, CPort, ctypes.c_void_p], None)
    fun("get_port", [CPort, ctypes.c_void_p], CPort)

    fun("get_tag", [ctypes.c_int, ctypes.c_void_p], ctypes.c_int)
    fun("get_label", [ctypes.c_int, ctypes.c_void_p], ctypes.c_int)
    fun("get_port_target", [CPort, ctypes.c_void_p], ctypes.c_int)

    fun("set_dup_aux", [ctypes.c_int, CPort, CPort, ctypes.c_void_p], None)
    

  return local.lib

DEBUG.set(1)
lib = get_lib()


# def sides(tag:Tag, need_term:bool): return [i for i in range(3) if tag.negative_polarity(i) == need_term]

def serialize_term(term:Term, lib:ctypes.CDLL)->ctypes.c_void_p:
  rt = lib.new_runtime()
  cache = {}

  root = (Port(Node(Tag.ROOT), MAIN))


  wire(root, term.port)

  for node in term.port.node.walk(): cache[node] = lib.new_node(node.tag.value, node.label, rt)

  lib.set_root(cache[root.node], rt)


  for node in term.port.node.walk():

    def c_connect(node:Node, num:int):
      print("c_connect:", node, num )
      # p = to_c_port(target)
      # dest = CPort(cache[node], num)
      # src = CPort(cache[target.node], p)
      # print("set_port:", dest.loc, dest.side, src.loc, src.side)
      # lib.set_port(dest, src, rt)

    match node.tag:

      case Tag.App:
        for i in range(2): c_connect(node, i, node.con[same_ports(node.tag)[i]])
      case Tag.Lam:
        c_connect(node, 0)
        c_connect(node, 1)
      case Tag.Sup:
        c_connect(node, 0)
        c_connect(node, 1)
      
      case Tag.Dup:
        c_connect(node, 0)
        
        ps = []
        for i in range(2):
          port = node.con[AUX1 + i]
          ps.append(CPort(cache[port.node], to_c_port(port)))
      
        lib.set_dup_aux( cache[node], *ps, rt)
      
      case Tag.Null | Tag.ERA: pass
      case Tag.ROOT: c_connect(node, 0, node.con[MAIN])

      case Tag.Prim:
        if isinstance(node.value, int): 
          lib.set_port(CPort(cache[node], 0), CPort(node.value, 0), rt)
        elif isinstance(node.value, MathOps):
          lib.set_port(CPort(cache[node], 0), CPort(node.value.value, 1), rt)


      case _: raise ValueError(f"illegal node: {node}")


  return rt


def deserialize_term(rt:ctypes.c_void_p, lib:ctypes.CDLL):

  root = lib.get_root(rt)
  cache = {}

  def go(loc:int)->Node:
    if loc in cache: return cache[loc]

    node = Node(Tag(lib.get_tag(loc, rt)), lib.get_label(loc, rt))

    cache[loc] = node

    def connect(side:int):
      print(node.tag)

      p = CPort(loc, side)
      port : CPort = lib.get_port(p, rt)
      print("connect:", loc, side, port.loc, port.side)
      # tar = go(port.loc)
      # print("tar:", tar)

      # tarnum = from_c_port(tar.tag, port.side)
      # pass

      

    match node.tag:
      case Tag.ROOT:
        connect(0)
      case Tag.App:
        connect(0)
        connect(1)
      case Tag.Sup:
        connect(0)
        connect(1)
      case Tag.Lam:
        connect(1)
      case Tag.Dup:
        connect(0)
        """ you could get the other port from the aux ports but need to reverse xored data"""
      case Tag.Prim:
        port = lib.get_port(CPort(loc, 0),rt)
        if port.side: node.value = MathOps(port.loc)
        else: node.value = port.loc

    return node

  node = go(root)

  return Term(Port(node, MAIN).other())



def round_trip(term:Term):
  s = str(term)
  print(f"SER {s}")
  r = serialize_term(term, lib)
  d = deserialize_term(r, lib)
  assert str(d) == s, f"expected {s}, got {str(d)}"

t = Term(lambda x, y: x)
t2 = Term(lambda x, y: x)

t0 = Term(lambda x:x)

round_trip(Term.sup(t, t2))
round_trip(t0)
ds = t0.dups()
round_trip(Term(lambda x: ds[0](ds[1])))

round_trip(Term(lambda x: x + 1))
print("OK")


a = t(t2)

print(a)

r = serialize_term(a, lib)
res = lib.run(r)


res = deserialize_term(r, lib)
print(res)

