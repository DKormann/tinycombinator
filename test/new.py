from typing import Any
import unittest

from tinycombinator.helpers import print_tree
from tinycombinator.ic import AUX1, AUX2, Node, MAIN, Tag, parse_fun






class ConstructionRepresentation(unittest.TestCase):

  def _assert_fmt(self, term:Any, expected:str):
    with print_tree(False):
      self.assertEqual(str(Node(term)), expected)

  def test_id(self):

    self._assert_fmt(lambda x: x, "λa a")
    self._assert_fmt(lambda x, y: x, "λa λb a")
    self._assert_fmt(lambda x, y, z: x, "λa λb λc a")
  
  def test_app(self):
    a = Node(lambda x: x)
    b = Node(lambda y: y)
    self._assert_fmt(a(b), "( λa a λb b)")
  
  def test_sup(self):
    a = Node.sup(Node(lambda x: x), Node(lambda y: y), 0)
    self._assert_fmt(a, "&0{ λa a λb b}")
  
  def test_prim(self):
    a = Node(1)
    self._assert_fmt(a, "1")
  
  def test_add(self):
    a = Node(1) + Node(2)
    # self._assert_fmt(a, "( 1 + 2)")

    # print(a.tag, a.con[MAIN].target
    # print(a.tag, a.con[MAIN].target is a)

    # raise Exception("stop")

    self._assert_fmt(a, "(+ 1 2)")
  



if __name__ == "__main__":
  unittest.main()