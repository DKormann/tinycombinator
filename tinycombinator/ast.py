

from enum import Enum, auto
from typing import Callable, Generator, List

from tinycombinator.helpers import hide_dups, print_tree

from dataclasses import dataclass



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



# @dataclass
class Port:
  target: "IC"
  side: int



# @dataclass
class IC:
  ports: List[Port]
  tag: Tag
  label: int



# def tree(term:IC, ctx:dict[IC, int])->str:
#   ws = "  " if print_tree else ""
#   def varname(node:IC | None):
#     if node is None: return ""
#     name = chr(len(ctx) % 26 + 97) + ("" if len(ctx) < 26 else chr(len(ctx) // 26 + 97))
#     return ctx.setdefault(node, name)
#   def idn(lns:list[str], end = "")->list[str]:
#     lns = lns[:-1] + [lns[-1] + end]
#     if sum(len(ln) for ln in lns) <= 20: return [ws + " ".join(map(str.strip, lns))]
#     return [ws + ln for ln in lns]

#   def _tree(term:IC | None, dstack:list[tuple[int, bool]])->list[str]:
#     if term is None: return ["NONE"]
#     match term.tag:
#       case Tag.Lam: return [f"λ{varname(term.s1)} " + (p := _tree(term.s0, dstack))[0].strip()] + p[1:]
#       case Tag.Sup:
#         for i, (label, is_dup2) in reversed(list(enumerate(dstack))):
#           if term.label == label: return _tree(term.s1 if is_dup2 else term.s0, dstack[:i] + dstack[i+1:])
#         return [f"&{term.label}{{"] + idn(_tree(term.s0, dstack)) + idn(_tree(term.s1, dstack), "}")
        
#       case Tag.App: return [f"("] + idn(_tree(term.s0, dstack)) + idn(_tree(term.s1, dstack), ")")
#       case Tag.Dup | Tag.Dup2:
#         if hide_dups: return _tree(term.s0, dstack + ([(term.label, term.tag == Tag.Dup2)]))
#         d1 = term if (term.tag == Tag.Dup) else term.s1
#         d2 = term if (term.tag == Tag.Dup2) else term.s1
#         if d1 in ctx: return [varname(term)]
#         return [f"{varname(term)} where &{term.label}{{{varname(d1)}, {varname(d2)}}} ="] + idn(_tree(term.s0, dstack))

#       case Tag.Prim: return [str(term.label)]
#       case Tag.Null: return ["Nul"]
#     return [varname(term)]
#   return ("\n" if print_tree else " ").join(_tree(term, []))




def tree(ic: IC)->str:

  ws = "  " if print_tree else ""

  def idn(lns:list[str], end = "")->list[str]:
    lns = lns[:-1] + [lns[-1] + end]
    if sum(len(ln) for ln in lns) <= 20: return [ws + " ".join(map(str.strip, lns))]
    return [ws + ln for ln in lns]

  def go(ic: IC, dstack:list[tuple[int, bool]])->list[str]:
    match ic.tag:
      case Tag.Lam:
        return [f"λ"]
  
  return go(ic, [])




def ast_main():
  print(tree)