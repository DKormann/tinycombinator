

from enum import Enum, auto
from typing import Callable, Generator, List, Union

from tinycombinator.helpers import hide_dups, print_tree





class Tag(Enum):
  App = auto()
  Lam = auto()
  Sup = auto()
  Dup = auto()
  Dup2 = auto()
  Null = auto()
  Prim = auto()
  Freed = auto()

  intermediate_var = auto()

  def __str__(self)->str: return self.name
  def __repr__(self)->str: return self.name



class Port:
  def __init__(self, target: "IC", side: int = 0):
    self.target = target
    self.side = side



class IC:
  def __init__(self, tag: Tag, label: int = 0, s0: Union[Port, "IC", None] = None, s1: Union[Port, "IC", None] = None):
    self.tag = tag
    self.label = label
    self.s = [
      None if s is None else (s if isinstance(s, Port) else Port(s, 0))
      for s in [s0, s1]
    ]






def tree(term:IC)->str:
  ws = "  " if print_tree else ""
  ctx = {}
  def varname(node:IC | None):
    if node is None: return ""
    name = chr(len(ctx) % 26 + 97) + ("" if len(ctx) < 26 else chr(len(ctx) // 26 + 97))
    return ctx.setdefault(node, name)
  def idn(lns:list[str], end = "")->list[str]:
    lns = lns[:-1] + [lns[-1] + end]
    if sum(len(ln) for ln in lns) <= 20: return [ws + " ".join(map(str.strip, lns))]
    return [ws + ln for ln in lns]
  
  def _tree(term:Port)->list[str]:
    if term is None: return ["NONE"]
    if (term.side == 1): return [varname(term.target)]
    term = term.target
    match term.tag:
      case Tag.Lam: return idn([f"λ" + varname(term)] + _tree(term.s[0]))
      case Tag.App: return idn(_tree(term.s[0])) + idn(_tree(term.s[1]))
      case Tag.Sup: return idn([f"&{term.label}{{{varname(term.s[0])}, {varname(term.s[1])}}}"])
      case Tag.Dup: return idn([f"{varname(term)} where &{term.label}{{{varname(term.s[0])}, {varname(term.s[1])}}} ="] + _tree(term.s[0]))
      case Tag.Dup2: return idn([f"{varname(term)} where &{term.label}{{{varname(term.s[0])}, {varname(term.s[1])}}} ="] + _tree(term.s[0]))
      case Tag.Null: return ["Nul"]
      case Tag.Prim: return [str(term.label)]
      case Tag.Freed: return ["Freed"]
      case Tag.intermediate_var: return [varname(term)]
  return ("\n" if print_tree else " ").join(_tree(Port(term)))





def ast_main():
  b = IC(Tag.Lam)
  a = IC(Tag.Lam, b, b)
  b.s[0] = Port(a, 1)

  

  print(tree(a))