from typing import Any
import unittest

from tinycombinator.helpers import Context, Env, hide_dups, print_tree
from tinycombinator.lib.terms import churchNat
from tinycombinator.nodes import Port
from tinycombinator.term import Term, ID, T, F, label_reset, step

basics = [ID, T, F, churchNat(2), ID()(ID)]
class ConstructionRepresentation(unittest.TestCase):

  def _assert_fmt(self, term:Any, expected:str, **envs):
    with print_tree(False), Context(**envs):
      if isinstance(expected, Term): expected = str(expected)
      self.assertEqual(str(Term(term)), expected)
  
  def test_fmt(self):

    self._assert_fmt(ID, "λa a")
    self._assert_fmt(ID(), "λa a")
    self._assert_fmt(T, "λa λ a")
    self._assert_fmt(T(), "λa λ a")
    self._assert_fmt(F, "λ λa a")

    self._assert_fmt(churchNat(0), "λ λa a")
    self._assert_fmt(churchNat(1), "λa λb ( a b)")
    self._assert_fmt(churchNat(2), "λa λb ( a ( a b))", hide_dups = True)
    label_reset()
    self._assert_fmt(churchNat(2), "λa λb ( c where &72{c, d} = a ( d b))", hide_dups = False)

  def test_clone(self):
    for term in basics:
      t = Term(term)
      self.assertEqual(str(t), str(t.clone()))

    c2 = Term(churchNat(2))
    c2c = c2.clone()
    c2string = str(c2)
    c2.srcs[0].port.target.con[1] = None
    assert str(c2) != c2string
    assert str(c2c) == c2string
  
  def test_step(self):
    t = ID()(ID())
    res = step(t)
    self._assert_fmt(res, ID())







if __name__ == "__main__":
  unittest.main()