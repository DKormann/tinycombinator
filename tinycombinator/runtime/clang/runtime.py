import ctypes
from email.policy import default
import hashlib
import os
from pathlib import Path
from re import I
from tinycombinator.helpers import DEBUG, debug
from tinycombinator.nodes import PN, Node, Port, Tag, wire, MathOps
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
    case Tag.App: return [PN.MAIN, PN.AUX1]
    case Tag.Lam | Tag.Sup: return [PN.AUX1, PN.AUX2]
    case Tag.Dup: return [PN.MAIN, PN.AUX1, PN.AUX2]
    case Tag.ROOT | Tag.ERA: return [PN.MAIN]
  return []

# def encoded_ports(tag:Tag):
#   return [
#     [PN.MAIN, PN.AUX1],
#     *([[PN.AUX1, PN.AUX2]]*3),
#     *([[PN.MAIN]]*2),
#     [], []
#   ][tag.value]



def term_ports(tag:Tag): return [i for i in PN if tag.negative_polarity(i)]



term_ports

def is_subst(tag:Tag, num:int): return (tag == Tag.Lam and num == PN.AUX1) or (tag == Tag.Dup and num != PN.MAIN)

side = int
num = int




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

def serialize_term(term:Term, lib:ctypes.CDLL)->ctypes.c_void_p:
  rt = lib.new_runtime()
  cache = {}
  root = (Port(Node(Tag.ROOT), PN.MAIN))
  wire(root, term.port)
  for node in term.port.node.walk(): cache[node] = lib.new_node(node.tag.value, node.label, rt)
  lib.set_root(cache[root.node], rt)

  for node in term.port.node.walk():



    def to_c_side(port:Port) -> side:
      o = port.other()

      return (encoded_ports if is_subst(port.tag, port.number) else term_ports)(o.tag).index(o.number)


    def c_connect(side:int):
      portn = encoded_ports(node.tag)[side]
      lib.set_port(
        CPort(cache[node], side),
        CPort(cache[node.con[portn].node], to_c_side(Port(node, portn))),
        rt)

    match node.tag:
      case Tag.Dup:
        c_connect(0)
        ps = []
        for i in range(1,3):
          port = node.con[i]
          ps.append(CPort(cache[port.node], to_c_side(port)))
        lib.set_dup_aux( cache[node], *ps, rt)
      case Tag.Prim:
        if isinstance(node.value, int): lib.set_port(CPort(cache[node], 0), CPort(node.value, 0), rt)
        elif isinstance(node.value, MathOps): lib.set_port(CPort(cache[node], 0), CPort(node.value.value, 1), rt)
      case _:

        for i in range(len(encoded_ports(node.tag))):
          c_connect(i)



  return rt


def deserialize_term(rt:ctypes.c_void_p, lib:ctypes.CDLL):

  root = lib.get_root(rt)
  cache = {}

  def go(loc:int)->Node:
    if loc in cache: return cache[loc]
    node = Node(Tag(lib.get_tag(loc, rt)), lib.get_label(loc, rt))
    cache[loc] = node



    def connect(side:int, pn:PN):

      port: CPort = lib.get_port(CPort(loc, side), rt)
      o = go(port.loc)
      c_port = (encoded_ports if is_subst(node.tag, pn) else term_ports)(o.tag)[port.side]
      wire((node, pn),(o, c_port))

    match node.tag:
      case Tag.Dup:
        connect(0, PN.MAIN)
        """TODO"""
      case Tag.Prim:
        dat = lib.get_port(CPort(loc, 0), rt)
        node.value = MathOps(dat.loc) if dat.side else dat.loc
      case _:
        for i in enumerate(encoded_ports(node.tag)): connect(*i)
    return node

  node = go(root)

  return Term(Port(node, PN.MAIN).other())



def round_trip(term:Term):
  s = str(term)
  print(f"SER {s}")
  r = serialize_term(term, lib)
  d = deserialize_term(r, lib)
  assert str(d) == s, f"expected:\n {s}\ngot:\n {str(d)}"

t = Term(lambda x, y: x)
t2 = Term(lambda x, y: x)

t0 = Term(lambda x:x)

round_trip(Term.sup(t, t2))
round_trip(t0)
ds = t0.dups()

round_trip(Term(lambda x: ds[0](ds[1])))

os.system("clear")
round_trip(Term(lambda x: x + 1))
print("OK")


a = t(t2)

print(a)

r = serialize_term(a, lib)
res = lib.run(r)


res = deserialize_term(r, lib)
print(res)

