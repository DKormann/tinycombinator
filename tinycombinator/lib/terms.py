
from typing import Callable
from tinycombinator.ic import Node, Tag, app, lam, move, null, parse_lam, sup, x, dup
from tinycombinator.helpers import hide_dups


def id(): return lam(x(0))


def T(): return Node(lambda x, y: x)
def F(): return Node(lambda x, y: y)

def cnat(n:int):
  def go(n:int, f, x):
    if n == 0: return x
    return f(go(n-1, f, x))
  return Node(lambda f, x: go(n, f, x))

def circular(option1:int, option2:int):
  aux = [null(), null()]
  dups = dup(sup(aux[0], aux[1], 0), 0)
  move(dups[option1], aux[option2])
  return dups[not option1]


def fmt_eq(a:Node, b:Node):
  return str(a) == str(b)

if __name__ == "__main__":
  # from main import run_term_c
  a = (cnat(2))
  hide_dups.set(True)
  print(a)
  hide_dups.set(False)
  print(a)


  # print(circular(0, 1))
