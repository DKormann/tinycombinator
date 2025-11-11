from dataclasses import dataclass, field
from enum import Enum, auto
from functools import cached_property
from typing import Any, Callable, Dict, List, Tuple, Union
from tinycombinator.helpers import hide_dups, print_tree, debug


"""

most straightforward implementation of the IC
fully bidirectional connected graph

"""

class Tag(Enum):
  App, Lam, Dup, Sup, Null, Prim, ERA, ROOT = range(8)
  def __str__(self)->str: return self.name
  def __repr__(self)->str: return self.name


  def negative_polarity(self, side: int)->int:
    match self:
      case Tag.App: return side == AUX2
      case Tag.Lam: return side != AUX2
      case Tag.Sup: return side == MAIN
      case Tag.Dup: return side != MAIN
      case Tag.ROOT | Tag.ERA: return False
      case Tag.Prim | Tag.Null: return True
      case _: raise ValueError(f"unknown tag: {self.node.tag}")



class MathOps(Enum):
  Add, Sub, Mul, Div, Mod, Pow, Eq, Ne, Lt, Gt = range(10)
  __str__ = __repr__ = lambda self: ["+", "-", "*", "/", "%", "^", "==", "!=", "<", ">"][self.value]



MAIN, AUX1, AUX2 = range(3)

@dataclass
class Node:
  tag: Tag
  label: int = 0
  value: int = 0
  con: List["Port"] = field(default_factory=lambda: [None, None, None])

  def __post_init__(self): assert isinstance(self.tag, Tag)

  def walk(self):
    seen = {self}
    todo = [self]
    while todo:
      term = todo.pop()
      yield term
      for s in term.con:
        if s and s.node and s.node not in seen:
          seen.add(s.node)
          todo.append(s.node)
  
  def clone(self):
    cache = {node: Node(node.tag, node.label, node.value) for node in self.walk()}
    for node in self.walk(): cache[node].con = [None if con is None else Port(cache[con.node], con.side) for con in node.con]
    return cache[self]

  
  def __hash__(self): return hash(id(self))
  def __repr__(self)->str: return f"<Node {self.tag}>"

@dataclass(frozen=True)
class Port:

  def __post_init__(self): assert isinstance(self.node, Node)

  node: Node
  side: int = 0

  def other(self): return self.node.con[self.side]
  

  def is_term(self): return self.node.tag.negative_polarity(self.side)

  def __eq__(self, other: "Port"): return self.node is other.node and self.side == other.side
  def __hash__(self): return hash((id(self.node), self.side))


def wire(ic: Port, other: Port):
  ic, other = (Port(*p) if isinstance(p, tuple) else p for p in (ic, other))
  assert ic.is_term() != other.is_term(), f"cannot wire {ic} and {other}"
  ic.node.con[ic.side] = other
  other.node.con[other.side] = ic


