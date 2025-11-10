"""
Scott encoding for natural numbers and functions on them
"""

from operator import truediv
from tinycombinator.lib.terms import F, T, cnat
from tinycombinator.main import execute

from tinycombinator.nodes import  Node, Tag, app, hide_dups, lam, lamvar, move, null, parse_lam, print_tree, sup, x, dup



def nat(n:int)->Node:


  lam0, x0 = lamvar()
  lam0.s[0] = x0

  p = Node(Tag.Lam, lam0)

  for i in range(n):
    lam0 = Node(Tag.Lam)
    lams, xs = lamvar(lam0)
    lam0.s[0] = xs(p)
    p = lams
  return p


def iden()->Node:
  return Node(lambda x: x)


def Y_comb()->Node:
  return Node(lambda f: Node(lambda x: f(x(x))) (Node(lambda x: f(x(x)))))


def is_z()->Node:
  return Node(lambda n: n(
    lambda s: F(),
    T()
  ))

def rec0()->Node:
  return Node(
    lambda self, n: n(
      lambda s: self(s),
      nat(0)
    )
  )


def suc(x:Node)->Node:
  return Node( lambda s,z: s(x))

def rec_copy()->Node:
  return Node(
    lambda self, x: x(
      lambda s: suc(self(s)),
      nat(0)
    )
  )


def T()->Node: return Node(lambda t, f: t)

def F()->Node: return Node(lambda t, f: f)


def eq()->Node:
  return Y_comb()(
    lambda self, x, y: x(
      lambda px: y(
        lambda py: self(px, py),
        F
      ),
      y(
        lambda _: F,
        T
      )
    )
  )



def run_c_2_2():
  c = cnat(2)(cnat(2))
  run_term_c(c, 20, 20)

def run_scott_eq_3():
  N = 300
  c = eq()(nat(N), nat(N-1))
  run_term_c(c)
  


def try_era_var():
  c = dup(Node(F))[0]
  print(c)
  c = run_term_c(c)
  print(c)

if __name__ == "__main__":  


  run_scott_eq_3()


  pass
