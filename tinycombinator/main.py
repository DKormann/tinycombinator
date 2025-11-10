



from tinycombinator.helpers import hide_dups

from tinycombinator.term import ID, T, Term, parse_fun, run



class Node:

  def IF (c, t, f):
    c(t)(f )


if __name__ == "__main__":


  from tinycombinator.lib import church

  hide_dups.set(True)
  print(Term(church.Suc))





