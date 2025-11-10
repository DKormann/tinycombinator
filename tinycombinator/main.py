from tinycombinator.helpers import hide_dups

from tinycombinator.term import Term
from tinycombinator.lib import scott, church


class Node:
  def IF (c, t, f): c(t)(f)

@Term
def FN(f): return f + 1

if __name__ == "__main__":

  from tinycombinator.lib import church

  hide_dups.set(True)

  print(scott.nat(2))








