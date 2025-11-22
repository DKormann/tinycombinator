"""
Scott encoding for natural numbers and functions on them
"""
from tinycombinator.nodes import  Node, Tag
from tinycombinator.term import Ifun, Term, ID, T, F, Y_comb

def boolean(b:bool): return T() if b else F()

def nat(n:int)->Term:
  res = lambda s, z: z

  for _ in range(n):
    res = Term(lambda s, z: s(res))

  return Term(res)


def inc(): return Term(lambda t, s, z: s(t))
def dec(): return Term(lambda t: t(lambda p: p, t))

def to_z(): return Y_comb()(Term(
  lambda self, x:
    x(
      lambda p: self(p),
      x
    )
))

@Y_comb
def eq(self,x,y):
  return x(
      lambda p: y(
        lambda q: self(p,q),
        F()
      ),
      y(
        lambda q: F(),
        T()
      )
    )
