from typing import Callable, List, Tuple
from tinycombinator.helpers import DEBUG, hide_dups, print_tree, debug
from tinycombinator.nodes import Port, Tag, Node, wire, AUX1, AUX2, MAIN, MathOps
from tinycombinator.runtime.python import run as run_node


class Term:
  def __init__(self, x: Port | Node | int | Callable, side: int = None):
    if hasattr(self, "port"): return

    if isinstance(x, Port): pass
    elif isinstance(x, int): x = Port(Node(Tag.Prim, value = x))
    elif isinstance(x, Node): x = Port(x)
    elif callable(x):
      if x.__code__.co_argcount == 0: x = x()
      else: x = parse_fun(x)
    else: raise ValueError(f"invalid type: {type(x)}")
    if not x.is_term(): raise ValueError(f"not a term: {x}")
    self.port = x
  
  def __new__(cls, x, *args, **kwargs):

    if isinstance(x, Term): return x
    if callable(x):
      if x.__code__.co_argcount == 0:
        return x()
      else:
        x = parse_fun(x)
  
    return super().__new__(cls)

  def __repr__(self)->str: return decompile(self)

  def dups(self, label: int = None):
    if label is None: label = fresh_label()
    d = Node(Tag.Dup, label = label)
    wire(Port(d, MAIN), self.port)
    return Term(Port(d, AUX1)), Term(Port(d, AUX2))

  def binary(self, other: "Term", tag: Tag, sides: Tuple[int, int] = (AUX1, AUX2, MAIN), label: int = None):
    self, other = Term(self), Term(other)
    res = Node(tag, label = label)
    wire(Port(res, sides[0]), self.port)
    wire(Port(res, sides[1]), other.port)
    return Term(Port(res, sides[2]))

  def sup(self, other: "Term", label: int = None): return Term.binary(self, other, Tag.Sup, label  = fresh_label() if label is None else label)

  def __call__(self, *args: "Term"):
    res = self
    for arg in args:
      res = Term.binary(res, arg, Tag.App, (MAIN, AUX1, AUX2))
    return res
  

  @property
  def srcs(self)->List["Term"]:
    tars = []

    match self.port.node.tag:
      case Tag.App: tars = [MAIN, AUX1]
      case Tag.Lam: tars = [AUX2]
      case Tag.Null | Tag.Prim: return []
      case Tag.Dup: tars = [MAIN]
      case Tag.Sup: tars = [AUX1, AUX2]

    return [Term(self.port.node.con[i]) for i in tars]

  @staticmethod
  def binapp(op: MathOps):
    def fn(self, other: "Port"): return Term(Node(Tag.Prim, value = op))(self)(other)
    return fn

  __add__ = binapp(MathOps.Add)
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
    return Term(Port(self.port.node.clone(), self.port.side))


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
  def _tree(term:Port | None, stack:list[tuple[int, int]])->list[str]:

    if not term.is_term(): return [f"<CANT TREE: {term.node.tag}, {term.side}>"]

    if term is None: return ["NONE"]
    if term in ctx: return [varname(term)]
    node = term.node
    if node in ctx: return [varname(node)]

    match node.tag:
      case Tag.App: return ["("] + idn(_tree(node.con[MAIN], stack) + _tree(node.con[AUX1], stack), ")")
      case Tag.Lam:
        if term.side == AUX1: return [varname(node)]
        return [f"λ" + (varname(node) if node.con[AUX1].node.tag != Tag.ERA else "" )] + idn(_tree(node.con[AUX2], stack))
      case Tag.Dup:
        if hide_dups: return _tree(node.con[MAIN], [*stack, (term.node.label, term.side)])
        if term in ctx: return [varname(term)]
        names = [varname(Port(term.node, AUX1)), varname(Port(term.node, AUX2))]
        return [f"{names[term.side-1]} where &{node.label}{{{names[0]}, {names[1]}}} ="] + idn(_tree(node.con[MAIN], stack))

      case Tag.Sup:
        for i, (label, side) in enumerate(stack):
          if label == node.label: return _tree(node.con[side], [*stack[:i], *stack[i+1:]])
        return [f"&{node.label}{{"] + idn(_tree(node.con[AUX1], stack) + _tree(node.con[AUX2], stack), "}")
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
  assert isinstance(res, Port), f"expected Port, got {type(res)}"
  lam = Node(Tag.Lam)
  wire(Port(lam, AUX2), res)
  prev = None

  bindr = Term(Port(lam, AUX1))

  for node in lam.walk():
    for i,p in enumerate(node.con):
      if p is None or (p.node is lam and p.side == AUX1): continue
      if p.node is x.node:
        cur = Port(node, i)
        if prev is None:
          prev = cur
          wire(prev, bindr.port)
        else:
          ds = bindr.dups()
          wire(prev, ds[0].port)
          wire(cur, ds[1].port)
          prev = Port(ds[0].port.node, MAIN)

  if lam.con[AUX1] is None: wire(Port(lam, AUX1), Port(Node(Tag.ERA)))
  return Port(lam)

def ID(): return Term(lambda x: x)
def T(): return Term(lambda x, y: x)
def F(): return Term(lambda x, y: y)

def step(term: Term): return run(term, 1)

def run(term: Term, steps: int = None):
  root = Node(Tag.ROOT)
  wire(Port(root, MAIN), term.port)
  run_node(root, steps)
  return Term(root.con[MAIN])
