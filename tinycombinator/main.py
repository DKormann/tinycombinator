import os
from pathlib import Path
from tinycombinator.helpers import DEBUG, hide_dups

from tinycombinator.term import BACKEND, Term
from tinycombinator.lib import scott, church


class Node:
  def IF (c, t, f): c(t)(f)

@Term
def FN(f): return f + 1


def compare(t:Term):

  s = str(t)

  print(s)

  with BACKEND("python_simple") :
    r1 = t.run()
  with BACKEND("clang"), DEBUG(1):
    r2 = t.run()
  

  
  assert str(r1) == str(r2), f"\n{str(r1)} != \n{str(r2)}"
  print(f"RESULT: {r2}\n\n")


if __name__ == "__main__":


  compare(Term(lambda x: x)(lambda y: y))

  compare(Term(lambda x,y: x)(lambda x:x))
  compare(Term(lambda x,y: y)(lambda x:x))




    # compare(Term(
    #   lambda x: Term(lambda z, y:y)(x)
    # ))

