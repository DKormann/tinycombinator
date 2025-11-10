from tinycombinator.nodes import Node, Port, Tag, wire, AUX1, AUX2, MAIN, MathOps
from tinycombinator.helpers import debug


def erase(era:Node, app:Node)->Node:
  debug(f"erase {era} {app}")
  ers = [Node(era.tag, era.label, era.value) for i in range(2)]
  wire(Port(ers[1], MAIN), app.con[AUX1])
  wire(Port(ers[0], MAIN), app.con[AUX2]) # doesnt work?

def anihilate(app: Node, lam: Node)->Node:
  debug(f"anihilate {app} {lam}")
  if app.con[1] and lam.con[1]: wire(app.con[1], lam.con[1])
  if app.con[2] and lam.con[2]: wire(app.con[2], lam.con[2])

def commute(dup: Node, lam: Node)->Node:

  debug(f"commute {dup} {lam}")
  tags = (dup.tag, lam.tag)
  d2tag = Tag.Sup if tags == (Tag.Dup, Tag.Lam) else dup.tag
  l2tag = Tag.Dup if tags == (Tag.App, Tag.Sup) else lam.tag

  new = [[Node(dup.tag, dup.label), Node(d2tag, dup.label)], [Node(lam.tag, lam.label), Node(l2tag, lam.label)]]

  for i in range(4): wire(Port(new[i//2][i%2], MAIN), [dup, lam][1-i//2].con[2-i%2])
  for i in range(4): wire(Port(new[1][i//2], AUX1+i%2), Port(new[0][1-i%2], AUX2-i//2))

def redex(node: Node):
  if node.con[MAIN].side != MAIN: return False
  other = node.con[0].target
  match node.tag, other.tag:
    case (Tag.Null, Tag.Dup) | (Tag.Prim, Tag.Dup): erase(node, other)
    case (Tag.App, Tag.Lam): anihilate(node, other)
    case (Tag.Dup, Tag.Lam) | (Tag.App, Tag.Sup): commute(node, other)
    case (Tag.Dup, Tag.Sup):
      if node.label == other.label: anihilate(node, other)
      else: commute(node, other)
    case _: return False
  return True

def step(term: Node):

  for port in term.walk():
    if port and redex(port): break
  

