from math import exp
import unittest

from tinycombinator.lib.terms import circular, cnat

from tinycombinator.lib import scott
from tinycombinator.main import get_lib, get_node_count_c, load_term_c, run_term_c
from tinycombinator.nodes import Node, reset_labels
from tinycombinator.helpers import DEBUG, hide_dups, print_tree


hide_dups.set(True)
print_tree.set(False)




def assert_fmt(term:Node, expected:str|Node):

  if isinstance(expected, Node): expected = str(expected)
  with print_tree(False):
    assert str(term) == expected, f"Expected {expected}, got {str(term)}"

def assert_normal_fmt(term:Node, expected:str | Node):
  if isinstance(expected, Node):
    expected = run_term_c(expected)
  term = run_term_c(term)
  assert_fmt(term, expected)    


class TestAlloc(unittest.TestCase):
  def test_alloc(self):
    term = Node(lambda x: x)
    load_term_c(term)
    # assert get_node_count_c() == 1


class TestFormat(unittest.TestCase):
  def test_fmt(self):
    term = Node(lambda x: x)
    assert_fmt(term, "λa a")
    assert_fmt(term(1), "( λa a 1)")
  
  def test_fmt_app(self):
    term = Node(lambda x: x)
    assert_fmt(term, "λa a")
    assert_fmt(term(1), "( λa a 1)")
  
  def test_fmt_cnat(self):

    with hide_dups(False):
      reset_labels()
      assert_fmt(cnat(1), "λa λb ( a b)")
      assert_fmt(cnat(2), "λa λb ( c where &71{c, d} = a ( d b))")
  
  def test_fmt_snat(self):
    assert_fmt(scott.nat(0), "λ λa a")
    assert_fmt(scott.nat(1), "λa λ ( a λ λb b)")


class TestNormalization(unittest.TestCase):

  def test_id(self):
    def iden(): return Node(lambda x: x)
    assert_normal_fmt(iden(), "λa a")
    assert_normal_fmt(iden()(Node(None)), "Nul")
  
  def test_circular(self):
    for i in range(2):
      for j in range(2):
        term = circular(i, j)
        assert_normal_fmt(term, "Nul")
  
  def test_cnat(self):
    assert_normal_fmt(cnat(0), cnat(0))
    assert_normal_fmt(cnat(2)(cnat(2)), cnat(4))
  


class TestScott(unittest.TestCase):
  def test_rec_0(self):
    Y = scott.Y_comb()
    term = Y(scott.rec0())(scott.nat(2))
    assert_normal_fmt(term, "λ λa a")
  



