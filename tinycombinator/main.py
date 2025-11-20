import os
from pathlib import Path
from tinycombinator.helpers import DEBUG, Context, hide_dups

from tinycombinator.term import BACKEND, Term
from tinycombinator.lib import scott, church


class Node:
  def IF (c, t, f): c(t)(f)






if __name__ == "__main__":

  def compare(t:Term):
    t = Term(t)
    with BACKEND("python_simple"): p = str(t.run())[:1000]
    with BACKEND("clang"):r = str(t.run())[:1000]
    if p!=r:
      print(t)
      print("should be:",p)
      print("is:",r)
      raise RuntimeError("DONT MATCH")
    # print("OK\n\n\n\n")



  # DEBUG.set(1)

  t = Term(lambda x, y, a: Term.sup(x, y, 0)(a))


  t = Term.sup(
      Term(lambda x:x),
      Term(None),
      0
    ).dups(0)[0]

  compare(t)

  t = Term.sup(
      Term(lambda x:x),
      Term(None),
      0
    ).dups(1)[0]

  compare(t)
  
  t = Term(
    lambda x, y: x(y)
  ).dups(0)[0]

  compare(t)

  compare(Term(lambda x,y:x))

  t = Term(
    lambda x,y:x
  ).dups(0)[0]

  compare(t)



  t = Term(lambda x:x)(Term(lambda y:y))

  compare(t)

  from tinycombinator.lib import scott

  t = scott.dec()(scott.nat(2))

  compare(t)

  t = Term(lambda x,y,z:
      (Term.sup(x,y, 0))(z)
    )
  compare(t)


  compare(scott.to_z()(scott.nat(2)))



  compare(Term(lambda x: (Term(lambda x,y:y)(x))))


  compare(Term.sup(1,2,0)(3))


  # DEBUG.set(2)
  # with hide_dups(1), BACKEND('clang'):
  #   print(Term(lambda x,y,z: Term.sup(x(z.dup(0)), y(z), 0)))

  


  print("=========OK=========\n\n\n\n")