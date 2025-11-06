"""
Scott encoding for natural numbers and functions on them
"""

from operator import truediv
from tinycombinator.lib.terms import F, T, cnat
from tinycombinator.main import execute

from tinycombinator.ast import  IC, Tag, app, hide_dups, lam, lamvar, move, null, parse_lam, print_tree, sup, x, dup



def nat(n:int)->IC:


  lam0, x0 = lamvar()
  lam0.s[0] = x0

  p = IC(Tag.Lam, lam0)

  for i in range(n):
    lam0 = IC(Tag.Lam)
    lams, xs = lamvar(lam0)
    lam0.s[0] = xs(p)
    p = lams
  return p


def iden()->IC:
  return IC(lambda x: x)


def Y_comb()->IC:
  return IC(lambda f: IC(lambda x: f(x(x))) (IC(lambda x: f(x(x)))))


def is_z()->IC:
  return IC(lambda n: n(
    lambda s: F(),
    T()
  ))

def rec0()->IC:
  return IC(
    lambda self, n: n(
      lambda s: self(s),
      nat(0)
    )
  )


def suc(x:IC)->IC:
  return IC( lambda s,z: s(x))

def rec_copy()->IC:
  return IC(
    lambda self, x: x(
      lambda s: suc(self(s)),
      nat(0)
    )
  )


def T()->IC: return IC(lambda t, f: t)

def F()->IC: return IC(lambda t, f: f)


def eq()->IC:
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
  c = dup(IC(F))[0]
  print(c)
  c = run_term_c(c)
  print(c)

if __name__ == "__main__":  


  run_scott_eq_3()


  pass
