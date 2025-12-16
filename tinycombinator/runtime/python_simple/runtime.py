import functools
from typing import Generator, List
from tinycombinator.nodes import Node, Port, Tag, wire, PN, MathOps
from tinycombinator.helpers import debug
from tinycombinator.term import F, T, Node, Term


def erase(era:Node, app:Node)->Node:
  ers = [Node(era.tag, era.label, era.value) for i in range(2)]
  wire(Port(ers[1], PN.MAIN), app.con[PN.AUX1])
  wire(Port(ers[0], PN.MAIN), app.con[PN.AUX2]) # doesnt work?

def anihilate(app: Node, lam: Node)->Node:
  if app.con[1] and lam.con[1]: wire(app.con[1], lam.con[1])
  if app.con[2] and lam.con[2]: wire(app.con[2], lam.con[2])

def commute(dup: Node, lam: Node)->Node:

  assert lam.con[PN.AUX1] is not None and lam.con[PN.AUX2] is not None, f"lam {lam} has no aux1 or aux2: {lam.con}"

  tags = (dup.tag, lam.tag)
  d2tag = Tag.Sup if tags == (Tag.Dup, Tag.Lam) else dup.tag
  l2tag = Tag.Dup if tags == (Tag.App, Tag.Sup) else lam.tag
  new = [[Node(dup.tag, dup.label), Node(d2tag, dup.label)], [Node(lam.tag, lam.label), Node(l2tag, lam.label)]]


  wire((new[0][0], 0), lam.con[2])
  wire((new[0][1], 0), lam.con[1])
  wire((new[1][0], 0), dup.con[2])
  wire((new[1][1], 0), dup.con[1])

  wire((new[1][0], 1), (new[0][1], 2))
  wire((new[1][0], 2), (new[0][0], 2))
  wire((new[1][1], 1), (new[0][1], 1))
  wire((new[1][1], 2), (new[0][0], 1))

def prim_exec(app: Node, prim:Node):
  arg = app.con[PN.AUX1]
  if arg.tag != Tag.Prim:
    wire((app, 0), arg)
    wire((app, 1), (prim, 0))
  else:
    if callable(prim.value):
      prim.value = prim.value(arg.node.value)
      if (isinstance(prim.value, bool)):
        wire(app.con[PN.AUX2], Term(prim.value).port)
        return
    else:
      prim.value = arg.node.value(prim.value)
    wire(app.con[PN.AUX2], (prim, 0))


def redex(node: Node):
  if node.con[PN.MAIN].number != PN.MAIN: return False
  other = node.con[PN.MAIN].node
  match node.tag, other.tag:
    case (Tag.Null, Tag.Dup) | (Tag.Prim, Tag.Dup) | (Tag.ERA, Tag.Sup): erase(node, other)
    case (Tag.Dup, Tag.Lam) | (Tag.App, Tag.Sup): commute(node, other)
    case (Tag.App, Tag.Lam): anihilate(node, other)
    case (Tag.Dup, Tag.Sup):
      if node.label == other.label: anihilate(node, other)
      else: commute(node, other)
    case (Tag.App, Tag.Prim): prim_exec(node, other)
    case _: return False
  return True

def step(node: Node)->bool:
  for x in node.walk():
    if redex(x): return True

def run(root: Node, steps: int = None):
  """reduces inplace"""
  assert root.tag == Tag.ROOT, f"expected ROOT, got {Node.tag}"
  if steps is None: steps = int(1e9)
  for _ in range(steps):
    if not step(root.con[PN.MAIN].node): break
