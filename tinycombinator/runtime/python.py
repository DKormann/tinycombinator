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

  assert lam.con[AUX1] is not None and lam.con[AUX2] is not None, f"lam {lam} has no aux1 or aux2: {lam.con}"

  debug(f"commute {dup} {lam}")
  tags = (dup.tag, lam.tag)
  d2tag = Tag.Sup if tags == (Tag.Dup, Tag.Lam) else dup.tag
  l2tag = Tag.Dup if tags == (Tag.App, Tag.Sup) else lam.tag

  new = [[Node(dup.tag, dup.label), Node(d2tag, dup.label)], [Node(lam.tag, lam.label), Node(l2tag, lam.label)]]


  wire(Port(new[0][0], 0), lam.con[2])
  wire(Port(new[0][1], 0), lam.con[1])
  wire(Port(new[1][0], 0), dup.con[2])
  wire(Port(new[1][1], 0), dup.con[1])

  wire(Port(new[1][0], 1), Port(new[0][1], 2))
  wire(Port(new[1][0], 2), Port(new[0][0], 2))
  wire(Port(new[1][1], 1), Port(new[0][1], 1))
  wire(Port(new[1][1], 2), Port(new[0][0], 1))

def redex(node: Node):
  if node.con[MAIN].side != MAIN: return False
  other = node.con[0].node
  match node.tag, other.tag:
    case (Tag.Null, Tag.Dup) | (Tag.Prim, Tag.Dup) | (Tag.ERA, Tag.Sup): erase(node, other)
    case (Tag.Dup, Tag.Lam) | (Tag.App, Tag.Sup): commute(node, other)
    case (Tag.App, Tag.Lam): anihilate(node, other)
    case (Tag.Dup, Tag.Sup):
      if node.label == other.label: anihilate(node, other)
      else: commute(node, other)
    case _: return False
  return True

def step(node: Node):
  for port in node.walk():
    if port and redex(port): return True
  

def run(node: Node, steps: int = None):
  if steps is None: steps = int(1e9)
  for _ in range(steps):
    if not step(node): break

  

