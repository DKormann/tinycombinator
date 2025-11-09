
from dataclasses import dataclass
from enum import Enum, auto
from functools import cached_property
from typing import Callable, Union

from tinycombinator.helpers import print_tree


class Tag(Enum):
  App = auto()
  Lam = auto()
  Sup = auto()
  Dup = auto()
  Null = auto()
  Prim = auto()
  Freed = auto()
  intermediate_var = auto()

  def __str__(self)->str: return self.name
  def __repr__(self)->str: return self.name

class Op(Enum):
  Add = auto()
  Sub = auto()
  Mul = auto()
  Div = auto()
  Mod = auto()
  Pow = auto()
  Eq = auto()
  Ne = auto()
  Lt = auto()
  Int = auto()

@dataclass()
class Port:
  target: "IC"
  side: int = 0

  def __post_init__(self):
    if self.target is not None:
      self.target = IC(self.target)

  def __hash__(self):
    return hash((id(self.target), self.side))


@dataclass()
class XorPort(Port):
  targets: tuple[Port, Port]

  def target(self, user: IC)


class IC:
  def __init__(self, tag: Tag,  s0: Union[Port, "IC", None] = None, s1: Union[Port, "IC", None] = None, label: int = 0,):
    if hasattr(self, 'tag'): return
    if isinstance(tag, IC): raise ValueError(f'IC cannot be initialized with another IC: {tag}')

    self.tag = tag
    self.label = label
    self.s = [None if s is None else (s if isinstance(s, Port) else Port(s, 0)) for s in [s0, s1]]
  def __new__(cls, tag: Tag, *args, **kwargs):
    if isinstance(tag, IC): return tag
    if callable(tag): return parse_fun(tag)
    if isinstance(tag, int):
      res = IC(Tag.Prim, label = Op.Int)
      res.value = tag
      return res
    res = super().__new__(cls)
    return res

  
  def __repr__(self)->str: return tree(self)
  
  def walk(self):
    seen = set()
    todo = [self]
    while todo:
      term = todo.pop()
      print(f'{term is None = }')
      yield term
      for s in term.s:
        if s and s.target and s.target not in seen:
          seen.add(s.target)
          todo.append(s.target)
    
  def __add__(self, other:"IC"): return IC(Tag.Prim, label = Op.Add)(self)(other)
  def __sub__(self, other:"IC"): return IC(Tag.Prim, label = Op.Sub)(self)(other)
  def __mul__(self, other:"IC"): return IC(Tag.Prim, label = Op.Mul)(self)(other)
  def __div__(self, other:"IC"): return IC(Tag.Prim, label = Op.Div)(self)(other)
  def __mod__(self, other:"IC"): return IC(Tag.Prim, label = Op.Mod)(self)(other)
  def __pow__(self, other:"IC"): return IC(Tag.Prim, label = Op.Pow)(self)(other)
  def __eq__(self, other:"IC"): return IC(Tag.Prim, label = Op.Eq)(self)(other)
  def __ne__(self, other:"IC"): return IC(Tag.Prim, label = Op.Ne)(self)(other)
  def __lt__(self, other:"IC"): return IC(Tag.Prim, label = Op.Lt)(self)(other)
  def __gt__(self, other:"IC"): return IC(Tag.Prim, label = Op.Gt)(self)(other)
  
  def copy(self):
    cache = {}
    def go(term:IC | None):
      if term is None: return None
      if term not in cache:
        cache[term] = IC(term.tag, label = term.label)
        cache[term].s = [Port(go(term.s[i].target), term.s[i].side) if term.s[i] is not None else None for i in range(2)]
        if hasattr(term, 'value'): cache[term].value = term.value
      return cache[term]
    return go(self)
  
  def sup(self, other:"IC", label=None): 
    if label is None:
      global lab_counter
      label = lab_counter
      lab_counter +=1
    return IC(Tag.Sup, self, other, label = label)

  
  def dup(self, label=None):
    if label is None:
      global lab_counter
      label = lab_counter
      lab_counter +=1
    return IC(Tag.Dup, self, label = label)
  

  def dups(self, label =None):
    d = self.dup(label)
    return Port(d, 0), Port(d, 1)

  def __hash__(self): return hash(id(self))
  
  def __call__(self, other:"IC"):
    return IC(Tag.App, self, other)





lab_counter = 70



def tree(term:IC)->str:
  ws = "  "
  ctx = {}
  def varname(node:IC | None):
    if node is None: return ""
    name = chr(len(ctx) % 26 + 97) + ("" if len(ctx) < 26 else chr(len(ctx) // 26 + 97))
    return ctx.setdefault(node, name)
  def idn(lns:list[str], end = "")->list[str]:
    lns = lns[:-1] + [lns[-1] + end]
    if sum(len(ln) for ln in lns) <= 20: return [ws + " ".join(map(str.strip, lns))]
    return [ws + ln for ln in lns]
  
  def _tree(port:Port | None)->list[str]:

    if port is None: return ["NONE"]
    term = port.target
    if term in ctx: return [varname(term)]
    if (port.side == 1): return [varname(term)]
    match term.tag:
      case Tag.Lam: return [f"λ"] + idn([(varname(term) if term.s[1] else "" )] + _tree(term.s[0]))
      case Tag.App: return ["("] + idn(_tree(term.s[0]) + _tree(term.s[1]), ")")
      case Tag.Sup: return [f"&{term.label}{{"] + idn(_tree(term.s[0]) + _tree(term.s[1]), "}")
      case Tag.Dup:
        dummy = varname((term, 0))
        real = varname(term)
        names = [real, dummy] if port.side else [dummy, real]
        return [f"{dummy} where &{term.label}{{{names[0]}, {names[1]}}} ="] + idn(_tree(term.s[0]))

      case Tag.Prim:
        if term.label == Op.Int: return [str(term.value)]
        if term.label == Op.Add: return ["+"]
        return ["IC:"+str(term.label)]



      case _: return ["IC:"+str(term.tag)]
  return ("\n" if print_tree else " ").join(_tree(Port(term))).strip()

def curried(fun: Callable, argc: int = None)->Callable:
  if isinstance(fun, IC):return fun
  if callable(fun):
    if argc is None:argc = fun.__code__.co_argcount
    if argc == 0: return fun()
    if argc == 1: return fun
    return lambda x: curried(lambda *args: fun(x, *args), argc-1)

def parse_fun(lam: Callable)->IC:
  x = IC(Tag.intermediate_var)
  if lam.__code__.co_argcount > 1: lam = curried(lam)
  lam = IC(Tag.Lam, IC(lam(x)))
  for term in lam.walk():
    for s in range(2):
      if term.s[s] and term.s[s].target is x:
        term.s[s] = Port(lam, 1)
        lam.s[1] = Port(term, s)
        return lam
  lam.s[1] = None
  return lam


def ast_main():

  f = lambda x,y: y
  a = parse_fun(f)

  print(tree(a))
