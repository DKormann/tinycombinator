"""
Scott encoding for natural numbers and functions on them
"""
from tinycombinator.nodes import  Node, Tag
from tinycombinator.term import Term


def nat(n:int)->Term:
  res = lambda s, z: z

  for _ in range(n):
    res = Term(lambda s, z: s(res))

  return Term(res)


def Y_comb()->Term:
  return Term(lambda f: Term(lambda x: f(x(x))) (Term(lambda x: f(x(x)))))



def inc(): return Term(lambda t, s, z: s(t))
def dec(): return Term(lambda t: t(lambda p: p, t))

# print(inc())
# print(dec())

# def is_z()->Term:
#   return Term(lambda n: n(
#     lambda s: F(),
#     T()
#   ))

# def rec0()->Term:
#   return Term(
#     lambda self, n: n(
#       lambda s: self(s),
#       nat(0)
#     )
#   )


# def suc(x:Term)->Term:
#   return Term( lambda s,z: s(x))

# def rec_copy()->Term:
#   return Term(
#     lambda self, x: x(
#       lambda s: suc(self(s)),
#       nat(0)
#     )
#   )


# def T()->Term: return Term(lambda t, f: t)

# def F()->Term: return Term(lambda t, f: f)


# def eq()->Term:
#   return Y_comb()(
#     lambda self, x, y: x(
#       lambda px: y(
#         lambda py: self(px, py),
#         F
#       ),
#       y(
#         lambda _: F,
#         T
#       )
#     )
#   )
