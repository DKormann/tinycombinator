
from enum import Enum, auto
from typing import Callable, Generator

from tinycombinator.helpers import hide_dups, print_tree




class Tag(Enum):
  App = auto()
  Lam = auto()
  Sup = auto()
  Dup = auto()
  Dup2 = auto()
  Null = auto()
  Var = auto()
  Freed = auto()
  Prim = auto()
  # Mat = auto()
  # Dat = auto()

  intermediate_var = auto()

  def __str__(self)->str: return self.name
  def __repr__(self)->str: return self.name


class IC:
  def __init__(self, tag: Tag | None | Callable | int = None, s0:"IC" = None, s1:"IC" = None, label:int = None):
    if tag is None: tag = Tag.Null
    self.s0 = None if s0 is None else IC.into(s0)
    self.s1 = None if s1 is None else IC.into(s1)
    self.label = label
    if isinstance(tag, Tag): self.tag = tag
    else: move(IC.into(tag),self)
  def __str__(self)->str: return tree(self, {})
  def __repr__(self)->str: return str(self)
  def dup(self, label:int = None)->"IC":
    ds = dup(move(self), label)
    move(ds[0], self)
    return ds[1]
  def srcs(self):
    res = []
    if self.tag in [Tag.Lam, Tag.Dup, Tag.Dup2, Tag.App, Tag.Sup]: res.append(self.s0)
    if self.tag in [Tag.App, Tag.Sup]: res.append(self.s1)
    return res
  
  def set_port(self, side: int, port: "IC"):
    if side == 0: self.s0 = port
    else: self.s1 = port
  
  def all_srcs(self):
    seen = set()
    todo = [self]
    while todo:
      node = todo.pop()
      if node in seen or node is None: continue
      seen.add(node)
      todo.extend([node.s0, node.s1])
      yield node
    


  @staticmethod
  def into(arg)->"IC":
    if hasattr(arg, "ic"): return arg.ic()

    if isinstance(arg, IC): return arg
    if callable(arg):

      if arg.__code__.co_argcount == 0: return arg()

      l = IC(Tag.Lam, null(), None)
      v = IC(Tag.Var, l)
      l.s1 = v
      l.s0 = IC.into(mk_curried(arg)(v))

      found = False
      def arg_dups(arg:IC):
        nonlocal found
        if arg == v:
          if found: return v.dup()
          found = True
        if arg.tag in [Tag.Dup, Tag.Dup2, Tag.App, Tag.Sup, Tag.Lam]: arg.s0 = arg_dups(arg.s0)
        if arg.tag in [Tag.App, Tag.Sup]: arg.s1 = arg_dups(arg.s1)
        return arg

      arg_dups(l.s0)
      if not found: l.s1 = None
      return l
    if (isinstance(arg, int)): return IC(Tag.Prim, label = arg)
    if arg is None: return IC(Tag.Null)
  
  def __call__(self, *args:"IC")->"IC":
    if not args: return self
    return app(self, args[0])(*args[1:])
  

  def copy(self)->"IC":
    from tinycombinator.main import from_c_data, to_c_data
    return from_c_data(to_c_data(self))
  
  def run(self)->"IC":
    from tinycombinator.main import execute
    return execute(self)
  


def mk_curried(arg:Callable)->Callable:
  args = []
  def curried(x:IC)->IC:
    args.append(x)
    if len(args) == arg.__code__.co_argcount: return arg(*args)
    return curried
  return curried



def x(var:int) -> IC: return IC(Tag.intermediate_var, label = var)

def num(n:int) -> IC: return IC(Tag.Prim, label = n)

def var(lam:IC) -> IC:
  lam.s1 = IC(Tag.Var, lam)
  lam.s1.s0 = lam
  return lam.s1

def app(func:IC, arg:IC) -> IC: return IC(Tag.App, func, arg)

ilab = 70

def reset_labels():
  global ilab
  ilab = 70

def sup(a:IC, b:IC, label:int = None)->IC:
  global ilab
  if label is None: label = (ilab := ilab + 1)
  return IC(Tag.Sup, a, b, label)

def dup(s0:IC, label:int = None)->tuple[IC, IC]:
  global ilab
  if label is None: label = (ilab := ilab + 1)
  d = IC(Tag.Dup, s0, label = label)
  d2 = IC(Tag.Dup2, s0, d, label)
  d.s1 = d2
  d2.s1 = d
  return d, d2



def null(): return IC(Tag.Null)


def lam(body:IC) -> IC:
  res = IC(Tag.Lam, body)
  parse_lam(res, body, 0)
  return res

def move(src:IC, dst:IC | None = None)->IC:
  if dst is None: dst = IC(None)
  if isinstance(src, list) or isinstance(src, tuple): return [move(s, d) for s, d in zip(src, dst)]

  dst.tag = src.tag
  dst.s0 = src.s0
  dst.s1 = src.s1
  dst.label = src.label
  if src.tag == Tag.Var:
    lam = src.s0
    assert lam.tag == Tag.Lam
    lam.s1 = dst
  if src.tag == Tag.Lam and src.s1 is not None:
    dst.s1.s0 = dst
  if src.tag in [Tag.Dup, Tag.Dup2]:
    dst.s1.s1 =dst
  return dst


def lamvar(bod:IC|None = None)->tuple[IC, IC]:
  x = IC(Tag.Var)
  lam = IC(Tag.Lam, bod, x)
  x.s0 = lam
  return lam,x


def parse_lam(lam:IC, current:IC, depth:int):
  print("parse_lam", current.tag)
  if current.tag == Tag.Lam: parse_lam(lam, current.s0, depth + 1)
  elif current.tag in [Tag.App, Tag.Sup]: parse_lam(lam, current.s1, depth)
  elif current.tag in [Tag.Dup, Tag.Dup2, Tag.App, Tag.Sup]: parse_lam(lam, current.s0, depth)
  elif ((current.tag == Tag.intermediate_var and current.label == depth) or
        (current.tag == Tag.Var and current.s0 == lam and lam.s1 is not current)):
    if lam.s1 is None: move(var(lam), current)
    else:
      prev = lam.s1
      move(dup(var(lam)), [prev,current])

def tree(term:IC, ctx:dict[IC, int])->str:
  ws = "  " if print_tree else ""
  def varname(node:IC | None):
    if node is None: return ""
    name = chr(len(ctx) % 26 + 97) + ("" if len(ctx) < 26 else chr(len(ctx) // 26 + 97))
    return ctx.setdefault(node, name)
  def idn(lns:list[str], end = "")->list[str]:
    lns = lns[:-1] + [lns[-1] + end]
    if sum(len(ln) for ln in lns) <= 20: return [ws + " ".join(map(str.strip, lns))]
    return [ws + ln for ln in lns]

  def _tree(term:IC | None, dstack:list[tuple[int, bool]])->list[str]:
    if term is None: return ["NONE"]
    match term.tag:
      case Tag.Lam: return [f"λ{varname(term.s1)} " + (p := _tree(term.s0, dstack))[0].strip()] + p[1:]
      case Tag.Sup:
        for i, (label, is_dup2) in reversed(list(enumerate(dstack))):
          if term.label == label: return _tree(term.s1 if is_dup2 else term.s0, dstack[:i] + dstack[i+1:])
        return [f"&{term.label}{{"] + idn(_tree(term.s0, dstack)) + idn(_tree(term.s1, dstack), "}")
        
      case Tag.App: return [f"("] + idn(_tree(term.s0, dstack)) + idn(_tree(term.s1, dstack), ")")
      case Tag.Dup | Tag.Dup2:
        if hide_dups: return _tree(term.s0, dstack + ([(term.label, term.tag == Tag.Dup2)]))
        d1 = term if (term.tag == Tag.Dup) else term.s1
        d2 = term if (term.tag == Tag.Dup2) else term.s1
        if d1 in ctx: return [varname(term)]
        return [f"{varname(term)} where &{term.label}{{{varname(d1)}, {varname(d2)}}} ="] + idn(_tree(term.s0, dstack))

      case Tag.Prim: return [str(term.label)]
      case Tag.Null: return ["Nul"]
    return [varname(term)]
  return ("\n" if print_tree else " ").join(_tree(term, []))
