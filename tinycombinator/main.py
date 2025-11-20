import os
from pathlib import Path
from tinycombinator.helpers import DEBUG, hide_dups

from tinycombinator.term import BACKEND, Term
from tinycombinator.lib import scott, church


class Node:
  def IF (c, t, f): c(t)(f)






if __name__ == "__main__":

  # def compare(t:Term):
  #   t = Term(t)
  #   print(t)
  #   with BACKEND("python_simple"): p = str(t.run())[:1000]
  #   with DEBUG(1), BACKEND("clang"):r = str(t.run())[:1000]
  #   if p!=r:
  #     print("should be:",p)
  #     print("is:",r)
  #     raise RuntimeError("DONT MATCH")
  #   print("OK\n\n\n\n")



  # DEBUG.set(1)

  # t = Term(lambda x, y, a: Term.sup(x, y, 0)(a))


  # t = Term.sup(
  #     Term(lambda x:x),
  #     Term(None),
  #     0
  #   ).dups(0)[0]

  # compare(t)

  # t = Term.sup(
  #     Term(lambda x:x),
  #     Term(None),
  #     0
  #   ).dups(1)[0]

  # compare(t)
  
  # t = Term(
  #   lambda x, y: x(y)
  # ).dups(0)[0]

  # compare(t)

  # compare(Term(lambda x,y:x))

  # t = Term(
  #   lambda x,y:x
  # ).dups(0)[0]

  # compare(t)



  # t = Term(lambda x:x)(Term(lambda y:y))

  # compare(t)

  # from tinycombinator.lib import scott

  # t = scott.dec()(scott.nat(2))


  # compare(t)




  # t = Term(lambda x,y,z:
  #     (Term.sup(x,y, 0))(z)
  #   )
  # compare(t)


  # compare(scott.to_z()(scott.nat(2)))

  from tinycombinator.lib import scott

  t = scott.to_z()(scott.nat(1))

  print(t)

  print(t.run())

  print("=========OK=========\n\n\n\n")