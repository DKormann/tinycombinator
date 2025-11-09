from dataclasses import dataclass
from enum import Enum, auto
from functools import cached_property
from typing import Any, Callable, Dict, List, Tuple, Union

from tinycombinator.helpers import print_tree



"""

most straightforward implementation of the IC
fully bidirectional connected graph

"""

class Tag(Enum):
  App = auto()
  Lam = auto()
  Sup = auto()
  Dup = auto()
  Null = auto()
  Prim = auto()

  def __str__(self)->str: return self.name
  def __repr__(self)->str: return self.name


class MathOps(Enum):
  Add = auto()
  Sub = auto()
  Mul = auto()
  Div = auto()
  Mod = auto()
  Pow = auto()
  Eq = auto()
  Ne = auto()
  Lt = auto()
  Gt = auto()

MAIN = 0
AUX1 = 1
AUX2 = 2




@dataclass
class Node:

  def __init__(self, tag: Tag, label: int = 0, value: int = 0):
    if hasattr(self, 'tag'): return
    self.con : List[IC | None] = [None, None, None]
    self.label = label
    self.tag = tag
    self.value = value

  def walk(self):
    seen = set()
    todo = [self]
    while todo:
      term = todo.pop()
      yield term
      for s in term.con:
        if s and s.target and s.target not in seen:
          seen.add(s.target)
          todo.append(s.target)
  
  def copy(self):
    cache = {node: Node(node.tag, node.label, node.value) for node in self.walk()}
    for node in self.walk(): cache[node].con = [None if con is None else IC(con.target, con.side) for con in node.con]
    return cache[self]

  
  def __hash__(self): return hash(id(self))
  def __repr__(self)->str: return f"<{self.tag}>"

  @property
  def main(self)->"IC": return IC(self, MAIN)





class IC:
  def __init__(self, target: "Node" = None, side: int = None, *args, **kwargs):
    if target is None: raise ValueError("target cannot be None")
    if side is not None: self.side = side
    if not hasattr(self, 'side') or self.side is None: self.side = 0
    if not hasattr(self, 'target'): self.target = target

  
  def __new__(cls, target: Any, *args, **kwargs):
    if isinstance(target, IC): return IC(target.target, target.side, *args, **kwargs)
    if isinstance(target, Tag):
      target = Node(target, *args, **kwargs)
      return IC(target)
    if isinstance(target, int):
      res = Node(Tag.Prim, value = target)
      return IC(res)
    if callable(target):
      return parse_fun(target)
    res = super().__new__(cls)
    return res
  
  def copy(self):
    return IC(self.target.copy(), self.side)
  
  def __repr__(self)->str: return f"<{self.target.tag}, {self.side}>"
  def __hash__(self): return hash(id(self.target), self.side)
  def __eq__(self, other: "IC"): return self.target is other.target and self.side == other.side

  def is_term(self):

    match self.target.tag:
      case Tag.App: return self.side == AUX2
      case Tag.Lam: return self.side != AUX2
      case Tag.Sup: return self.side == MAIN
      case Tag.Dup: return self.side != MAIN
      case Tag.Prim: return True
      case Tag.Null: return True
    raise ValueError(f"unknown tag: {self.target.tag}")
  
  def binary(self, other: "IC", tag: Tag, sides: Tuple[int, int] = (AUX1, AUX2, MAIN)):
    res = Node(tag)
    wire(IC(res, sides[0]), self)
    wire(IC(res, sides[1]), IC(other))
    return IC(res, sides[2])

  def __call__(self, other: "IC"):
    return self.binary(other, Tag.App, (MAIN, AUX1, AUX2))

  @staticmethod
  def binapp(op: MathOps):
    def fn(self, other: "IC"): return IC(Tag.Prim, value = op)(self)(other)
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

def wire(ic: "IC", other: "IC"):
  ic.target.con[ic.side] = other
  other.target.con[other.side] = ic

  

lab_ctr = 70
def fresh_label()->int:
  global lab_ctr
  lab_ctr += 1
  return lab_ctr
  

def tree(term:IC)->str:
  ws = "  " if print_tree else ""
  ctx = {}
  def varname(node:Node | None):
    if node is None: return ""
    name = chr(len(ctx) % 26 + 97) + ("" if len(ctx) < 26 else chr(len(ctx) // 26 + 97))
    return ctx.setdefault(node, name)
  def idn(lns:list[str], end = "")->list[str]:
    lns = lns[:-1] + [lns[-1] + end]
    if sum(len(ln) for ln in lns) <= 20: return [ws + " ".join(map(str.strip, lns))]
    return [ws + ln for ln in lns]
  def _tree(port:IC | None)->list[str]:

    if port is None: return ["NONE"]
    node = port.target
    if node in ctx: return [varname(node)]
    # if (port.side == 1): return [varname(term)]

    match node.tag:
      case Tag.App: return ["("] + idn(_tree(node.con[MAIN]) + _tree(node.con[AUX1]), ")")
      case Tag.Lam:
        if port.side == AUX1: return [varname(node)]
        return [f"λ" + (varname(node) if node.con[AUX1] else "" )] + idn(_tree(node.con[AUX2]))
      case Tag.Dup:
        dummy = varname((term, 0))
        real = varname(term)
        names = [real, dummy] if port.side == AUX1 else [dummy, real]
        return [f"{dummy} where &{node.label}{{{names[0]}, {names[1]}}} ="] + idn(_tree(node.con[MAIN]))
      case Tag.Sup: return [f"&{node.label}{{"] + idn(_tree(node.con[AUX1]) + _tree(node.con[AUX2]), "}")
      case Tag.Prim:
        if isinstance(node.value, MathOps):
          return [str(node.value.name)]
        return [str(node.value)]
      case Tag.Null: return ["NULL"]
      case _: return ["IC:"+str(node.tag)]
  return ("\n" if print_tree else " ").join(_tree(term)).strip()
        

def curried(fun: Callable, argc: int = None)->Callable:
  if isinstance(fun, Node):return fun
  if callable(fun):
    if argc is None:argc = fun.__code__.co_argcount
    if argc == 0: return fun()
    if argc == 1: return fun
    return lambda x: curried(lambda *args: fun(x, *args), argc-1)

def parse_fun(fn: Callable)->IC:
  x = IC(Tag.Null)
  if fn.__code__.co_argcount > 1: fn = curried(fn)
  res = fn(x)
  bod = IC(res)

  lam = IC(Tag.Lam)
  wire(IC(lam.target, AUX2), bod)
  for node in lam.target.walk():

    for i,p in enumerate(node.con):
      if p is None or (p.target is lam and p.side == AUX1): continue

      if p.target is x.target:
        wire(
          IC(node, i),
          IC(lam, AUX1),
        )

        return lam
        

  return lam



if __name__ == "__main__":

  F = IC(lambda x, y: x + (y))

  print(tree(F))
  print(tree(F.copy()))