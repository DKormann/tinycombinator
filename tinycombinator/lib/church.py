"""

church encodings

"""


from tinycombinator.term import Term


def Nat(n:int)->Term:
  def res(s: Term, z: Term)->Term:
    for _ in range(n): z = s(z)
    return z
  return Term(res)

def Suc(n:Term)->Term:
  return Term(lambda s, z: s(n(s, z)))

