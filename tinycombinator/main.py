import os
from pathlib import Path
from tinycombinator.helpers import DEBUG, hide_dups

from tinycombinator.term import BACKEND, Term
from tinycombinator.lib import scott, church


class Node:
  def IF (c, t, f): c(t)(f)




if __name__ == "__main__":

  t = Term(lambda x, y, a: Term.sup(x, y, 0)(a))


  t = Term.sup(
      Term(lambda x:x),
      Term(None),
      0
    ).dups(0)[0]

  print(t)
  with BACKEND("clang"):
    print(t.run(), "\n\n\n\n")



  t = Term.sup(
      Term(lambda x:x),
      Term(None),
      0
    ).dups(1)[0]

  print(t)
  print(t.run())

  with BACKEND("clang"):
    print(t.run(), "\n\n\n\n")
  


  t = Term(
    lambda x, y: x(y)
  ).dups(0)[0]

  print(t)

  print(t.run())

  with BACKEND("clang"):
    print(t.run(), "\n\n\n\n")




  t = Term(
    lambda x,y:x
  ).dups(0)[0]

  print(t)

  print(t.run())

  with BACKEND("clang"):
    print(t.run(), "\n\n\n\n")

