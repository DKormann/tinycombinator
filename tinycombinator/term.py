import os
from pathlib import Path
from typing import Any, Callable, List, Tuple
from tinycombinator.helpers import DEBUG, Env, hide_dups, print_tree, debug
from tinycombinator.nodes import Port, Tag, Node, wire, PN, MathOps
import importlib


BACKEND = Env("BACKEND", "python_simple")
runtime_path = Path(__file__).parent/"runtime"

def backend_set(value):
  Env.set(BACKEND, value)
  assert (runtime_path/value).is_dir(), f"ERROR: no such backend {runtime_path/value}\noptions: {os.listdir(runtime_path)}"

BACKEND.set = backend_set

class Term:
  def __init__(self, x: Any):
    if x is None: x = Node(Tag.Null)
    if hasattr(self, "port"): return
    if isinstance(x, Port): pass
    elif isinstance(x, int): x = Port(Node(Tag.Prim, value = x))
    elif isinstance(x, Node): x = Port(x)
    elif callable(x):
      if x.__code__.co_argcount == 0: x = x()
      else: x = parse_fun(x)
    else: raise ValueError(f"invalid type: {type(x)}")
    if not x.is_term(): raise ValueError(f"not a term: {x}")
    self.port : Port = x
  
  __match_args__ = ('port',)
  
  def __new__(cls, x, *args, **kwargs):

    if isinstance(x, Term): return x
    if x is None: return Term(Node(Tag.Null))
    if callable(x):
      if x.__code__.co_argcount == 0: return x()
      else: x = parse_fun(x)
  
    return super().__new__(cls)

  def __repr__(self)->str: return decompile(self)

  def dups(self, label: int = None):
    if label is None: label = fresh_label()
    d = Node(Tag.Dup, label = label)
    wire(Port(d, PN.MAIN), self.port)
    
    res = Term(Port(d, PN.AUX1)), Term(Port(d, PN.AUX2))
    for t in res: wire(t.port, Port(Node(Tag.ERA)))
    return res


  def binary(self, other: "Term", tag: Tag, sides: Tuple[int, int] = (PN.AUX1, PN.AUX2, PN.MAIN), label: int = 0):
    self, other = Term(self), Term(other)
    res = Node(tag, label = label)
    wire(Port(res, sides[0]), self.port)
    wire(Port(res, sides[1]), other.port)
    return Term(Port(res, sides[2]))

  def sup(self, other: "Term", label: int = None): return Term.binary(self, other, Tag.Sup, label  = fresh_label() if label is None else label)

  def __call__(self, *args: "Term"):
    res = self
    for arg in args:
      res = Term.binary(res, arg, Tag.App, (PN.MAIN, PN.AUX1, PN.AUX2))
    return res
  

  @property
  def srcs(self)->List["Term"]:
    tars = []

    match self.port.node.tag:
      case Tag.App: tars = [PN.MAIN, PN.AUX1]
      case Tag.Lam: tars = [PN.AUX2]
      case Tag.Null | Tag.Prim: return []
      case Tag.Dup: tars = [PN.MAIN]
      case Tag.Sup: tars = [PN.AUX1, PN.AUX2]

    return [Term(self.port.node.con[i]) for i in tars]
  

  def named_field(self, tag, pos): return self.srcs[pos] if self.port.node.tag == tag else None

  def __getattr__(self, name: str)->"Term":
    if name == "body": return self.named_field(Tag.Lam, 0)
    if name == "fn": return self.named_field(Tag.App, 0)
    if name == "arg": return self.named_field(Tag.App, 1)
    if name == "node": return self.port.node
    if name == "side": return self.port.number
    if name == "tag": return self.node.tag
    return super().__getattr__(name)

  @staticmethod
  def binapp(op: MathOps):
    def fn(self, other: "Port"): return Term(Node(Tag.Prim, value = op))(self)(other)
    return fn

  __add__ = binapp(MathOps.Add)
  __radd__ = __add__
  __sub__ = binapp(MathOps.Sub)
  __mul__ = binapp(MathOps.Mul)
  __div__ = binapp(MathOps.Div)
  __mod__ = binapp(MathOps.Mod)
  __pow__ = binapp(MathOps.Pow)
  __eq__ = binapp(MathOps.Eq)
  __ne__ = binapp(MathOps.Ne)
  __lt__ = binapp(MathOps.Lt)
  __gt__ = binapp(MathOps.Gt)

  def __pos__(self): return Term(Node(Tag.Prim, value = MathOps.Add))(self)
  def __hash__(self): raise NotImplementedError("__hash__ is not implemented")


  def clone(self)->"Term":
    """deep copy of the term"""
    return Term(Port(self.port.node.clone(), self.port.number))

  def run(self, steps:int = 1000)->"Term":
    run : Callable[[Node, int], None] = importlib.import_module("tinycombinator.runtime." + BACKEND.value + ".runtime").run
    wire(Port(Node(Tag.ROOT)), self.port )
    root = Port(Node(Tag.ROOT))
    wire(root, self.clone().port)
    run(root.node, steps)
    return Term(root.other())

def fresh_label()->int:
  global lab_ctr
  lab_ctr += 1
  return lab_ctr

def label_reset():
  global lab_ctr
  lab_ctr = 70

label_reset()
  

def decompile(term:Term)->str:
  ws = "  " if print_tree else "" 
  ctx = {}
  def varname(node:Node | None):
    if node is None: return ""
    return ctx.setdefault(node, chr(len(ctx) % 26 + 97) + ("" if len(ctx) < 26 else chr(len(ctx) // 26 + 97)))
  def idn(lns:list[str], end = "")->list[str]:
    lns = lns[:-1] + [lns[-1] + end]
    if sum(len(ln) for ln in lns) <= 20: return [ws + " ".join(map(str.strip, lns))]
    return [ws + ln for ln in lns]
  def _tree(term:Port | Any, stack:list[tuple[int, int]])->list[str]:
    if term is None: return ["<CANT TREE: NONE>"]
    if not term.is_term(): return [f"<CANT TREE: {term.node.tag}, {term.number}>"]

    if term is None: return ["NONE"]
    if term in ctx: return [varname(term)]
    node = term.node
    if node in ctx: return [varname(node)]

    match node.tag:
      case Tag.App: return ["("] + idn(_tree(node.con[PN.MAIN], stack) + _tree(node.con[PN.AUX1], stack), ")")
      case Tag.Lam:
        if term.number == PN.AUX1: return [varname(node)]
        # if term.number == PN.AUX1: return ["<VAR>"]
        return [f"λ" + (varname(node) if node.con[PN.AUX1].node.tag != Tag.ERA else "" )] + idn(_tree(node.con[PN.AUX2], stack))
      case Tag.Dup:
        if hide_dups: return _tree(node.con[PN.MAIN], [*stack, (term.node.label, term.number)])
        if term in ctx: return [varname(term)]
        names = [varname(Port(term.node, PN.AUX1)), varname(Port(term.node, PN.AUX2))]
        return [f"{names[term.number.value-1]} where &{node.label}{{{names[0]}, {names[1]}}} ="] + idn(_tree(node.con[PN.MAIN], stack))

      case Tag.Sup:
        for i, (label, side) in enumerate(stack):
          if label == node.label: return _tree(node.con[side], [*stack[:i], *stack[i+1:]])
        return [f"&{node.label}{{"] + idn(_tree(node.con[PN.AUX1], stack) + _tree(node.con[PN.AUX2], stack), "}")
      case Tag.Prim:
        if isinstance(node.value, MathOps): return [str(node.value)]
        return [f"{node.value}"]
      case Tag.Null: return ["NULL"]
      case _: return ["IC:"+str(node.tag)]
  return ("\n" if print_tree else " ").join(_tree(term.port, [])).strip()

def curried(fun: Callable, argc: int = None)->Callable:
  if isinstance(fun, Node):return fun
  if callable(fun):
    if argc is None:argc = fun.__code__.co_argcount
    if argc == 0: return fun()
    if argc == 1: return fun
    return lambda x: curried(lambda *args: fun(x, *args), argc-1)

def parse_fun(fn: Callable)->Node:
  x = Port(Node(Tag.Null))
  if fn.__code__.co_argcount > 1: fn = curried(fn)
  res = fn(Term(x))
  if isinstance(res, Term): res = res.port
  if callable(res): res = parse_fun(res)
  res = Term(res).port
  assert isinstance(res, Port), f"expected Port, got {type(res)}"
  lam = Node(Tag.Lam)
  wire(Port(lam, PN.AUX2), res)
  prev = None

  bindr = Term(Port(lam, PN.AUX1))

  for node in lam.walk():
    for i ,p in enumerate(node.con):
      if p is None or (p.node is lam and p.number == PN.AUX1): continue
      if p.node is x.node:
        cur = Port(node, PN(i))
        if prev is None:
          prev = cur
          wire(prev, bindr.port)
        else:
          ds = bindr.dups()
          wire(prev, ds[0].port)
          wire(cur, ds[1].port)
          prev = Port(ds[0].port.node, PN.MAIN)

  if lam.con[PN.AUX1] is None: wire(Port(lam, PN.AUX1), Port(Node(Tag.ERA)))
  return Port(lam)

def Ifun(f:Callable):
  return lambda *args: Term(f)(*args)

@Ifun
def Y_comb(f:Term):
  return Term(lambda x: f(x(x))) (Term(lambda x: f(x(x))))

@Ifun
def ID(x:Term): return x

@Ifun
def T(x,y): return x

@Ifun
def F(x,y): return y



