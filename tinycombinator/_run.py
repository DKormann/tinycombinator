

from tinycombinator.ic import Node, lam, x, app, sup, dup, var, null, Tag, tree, move
from tinycombinator.helpers import DEBUG


def fun(bod:Node)->Node:
  v = Node(Tag.Var)
  res = Node(Tag.Lam, bod, v)
  v.s[0] = res
  return res


def debug(*args):
  global DEBUG
  if DEBUG: print(*args)

def num(n:int)->Node:
  return Node(Tag.Prim, label=n)


def step(term:Node)->bool:
  if term.tag in [Tag.Var, Tag.Prim, Tag.Null]: return
  other = term.s[0]
  if other is None: return
  debug("STEP:", term)
  match (term.tag, other.tag):
    case (Tag.App, Tag.Lam):
      if other.s[1]: move(term.s[1], other.s[1])
      move(other.s[0], term)
      return True
    case (Tag.App, Tag.Sup):
      da, db = dup(term.s[1], other.label)
      move(sup(app(other.s[0], da), app(other.s[1], db), other.label), term)
      return True
    case (Tag.App, Tag.Dup | Tag.Dup2):
      return step(other)
    case (Tag.App, Tag.Prim):
      match term.s[1].tag:
        case Tag.Prim:
          res = other.label(term.s[1].label)
          move(num(res), term)
          return True
        case Tag.Sup:
          pass
      return False

    case (Tag.App, _):
      return step(other)
    case (Tag.Dup | Tag.Dup2, other_tag):
      da, db = (term, term.s[1]) if term.tag == Tag.Dup else (term.s[1], term)
      match other_tag:
        case Tag.Sup:
          debug("STEP: dup | dup2 -> sup")
          if other.label == da.label:
            move(other.s[0], da)
            move(other.s[1], db)
          else:
            dup1 = dup(other.s[0], da.label)
            dup2 = dup(other.s[1], da.label)
            move(sup(dup1[0], dup2[0], other.label), da)
            move(sup(dup1[1], dup2[1], other.label), db)
          return True
        case Tag.Lam:
          debug("STEP: dup | dup2 -> lam")
          ba, bb = dup(other.s[0], term.label)
          funa, funb = fun(ba), fun(bb)
          if other.s[1]: move(sup(funa.s[1], funb.s[1], term.label), other.s[1])
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
      return step(term.s[0]) or step(term.s[1])
    case (Tag.Lam, on):
      return step(term.s[0])
  
  debug("NO interaction: ", term.tag, other.tag)
  return False


def reduce(term):
  while step(term): pass
  return  term


