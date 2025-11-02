

from tinycombinator.ast import IC, lam, x, app, sup, dup, var, null, Tag, tree, move
from tinycombinator.helpers import DEBUG


def fun(bod:IC)->IC:
  v = IC(Tag.Var)
  res = IC(Tag.Lam, bod, v)
  v.s0 = res
  return res


def debug(*args):
  global DEBUG
  if DEBUG: print(*args)

def num(n:int)->IC:
  return IC(Tag.Prim, label=n)


def step(term:IC)->bool:
  if term.tag in [Tag.Var, Tag.Prim, Tag.Null]: return
  other = term.s0
  if other is None: return
  debug("STEP:", term)
  match (term.tag, other.tag):
    case (Tag.App, Tag.Lam):
      if other.s1: move(term.s1, other.s1)
      move(other.s0, term)
      return True
    case (Tag.App, Tag.Sup):
      da, db = dup(term.s1, other.label)
      move(sup(app(other.s0, da), app(other.s1, db), other.label), term)
      return True
    case (Tag.App, Tag.Dup | Tag.Dup2):
      return step(other)
    case (Tag.App, Tag.Prim):
      match term.s1.tag:
        case Tag.Prim:
          res = other.label(term.s1.label)
          move(num(res), term)
          return True
        case Tag.Sup:
          pass
      return False

    case (Tag.App, _):
      return step(other)
    case (Tag.Dup | Tag.Dup2, other_tag):
      da, db = (term, term.s1) if term.tag == Tag.Dup else (term.s1, term)
      match other_tag:
        case Tag.Sup:
          debug("STEP: dup | dup2 -> sup")
          if other.label == da.label:
            move(other.s0, da)
            move(other.s1, db)
          else:
            dup1 = dup(other.s0, da.label)
            dup2 = dup(other.s1, da.label)
            move(sup(dup1[0], dup2[0], other.label), da)
            move(sup(dup1[1], dup2[1], other.label), db)
          return True
        case Tag.Lam:
          debug("STEP: dup | dup2 -> lam")
          ba, bb = dup(other.s0, term.label)
          funa, funb = fun(ba), fun(bb)
          if other.s1: move(sup(funa.s1, funb.s1, term.label), other.s1)
          move(funa, da)
          move(funb, db)
          return True
        case Tag.App:
          return step(other)
        case Tag.Prim | Tag.Null:
          move(move(other, da), db)
          return True
        case Tag.Var: return False
        case _:
          return step(other)
    case (Tag.Sup, on):
      return step(term.s0) or step(term.s1)
    case (Tag.Lam, on):
      return step(term.s0)
  
  debug("NO interaction: ", term.tag, other.tag)
  return False


def reduce(term):
  while step(term): pass
  return  term


