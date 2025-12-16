from dataclasses import dataclass, field
from enum import Enum, auto
from functools import cached_property
from math import isfinite
from multiprocessing.spawn import prepare
from typing import Any, Callable, Dict, List, Tuple, Union
from tinycombinator.helpers import hide_dups, print_tree, debug


"""

most straightforward implementation of the IC
fully bidirectional connected graph

"""

class PN(Enum):
  """PORT number from 0-3"""
  MAIN, AUX1, AUX2 = range(3)
  def __index__(self): return self.value
  def __repr__(self):return self.name




class Tag(Enum):
  App, Lam, Dup, Sup, Null, Prim, ERA, ROOT = range(8)
  def __str__(self)->str: return self.name
  def __repr__(self)->str: return self.name


  def negative_polarity(self, pn: PN)->int:
    match self:
      case Tag.App: return pn == PN.AUX2
      case Tag.Lam: return pn != PN.AUX2
      case Tag.Sup: return pn == PN.MAIN
      case Tag.Dup: return pn != PN.MAIN
      case Tag.ROOT | Tag.ERA: return False
      case Tag.Prim | Tag.Null: return True
      case _: raise ValueError(f"unknown tag: {self.node.tag}")

class MathOps(Enum):
  Add, Sub, Mul, Div, Mod, Pow, Eq, Ne, Lt, Gt = range(10)
  __str__ = __repr__ = lambda self: ["+", "-", "*", "/", "%", "^", "==", "!=", "<", ">"][self.value]
  def __call__(self, x): return lambda y: eval(f"{x} {self} {y}")
  __int__ = lambda self: self.value


@dataclass
class Node:
  tag: Tag
  label: int = 0
  value: int = 0
  con: List["Port"] = field(default_factory=lambda: [None, None, None])

  @property
  def main(self): return self.con[0]

  def __post_init__(self): assert isinstance(self.tag, Tag)

  def walk(self, seen = None):
    if seen is None: seen = set()
    seen.add(self)
    yield self
    for port in self.con:
      if port is None or port.node in seen: continue
      yield from port.node.walk(seen)
  
  def clone(self):
    cache = {node: Node(node.tag, node.label, node.value) for node in self.walk()}
    for node in self.walk(): cache[node].con = [None if con is None else Port(cache[con.node], con.number) for con in node.con]
    return cache[self]

  
  def __hash__(self): return hash(id(self))
  def __repr__(self)->str: return f"<Node {self.tag}>"



@dataclass(frozen=True)
class Port:

  node:Node
  number: PN

  def __init__(self, node: Node, number: PN = 0):
    if isinstance(number, int): number = PN(number)
    assert isinstance(node, Node)
    super().__setattr__("node", node)
    super().__setattr__("number", number)

  def other(self): return self.node.con[self.number]

  def is_term(self): return self.node.tag.negative_polarity(self.number)

  @property
  def tag(self): return self.node.tag 

  def __eq__(self, other: "Port"):
    # if not isinstance(other, Port): return

    return self.node is other.node and self.number == other.number
  def __hash__(self): return hash((id(self.node), self.number))


def wire(ic: Port, other: Port):

  ic, other = (Port(*p) if isinstance(p, tuple) else p for p in (ic, other))
  assert ic.is_term() != other.is_term(), f"cannot wire {ic} and {other}"
  ic.node.con[ic.number.value] = other
  other.node.con[other.number.value] = ic



