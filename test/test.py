from typing import Any
import unittest


from tinycombinator.helpers import Context, Env, hide_dups, print_tree
from tinycombinator.lib import church, scott
from tinycombinator.nodes import Node, Port, Tag, wire, PN
from tinycombinator.term import BACKEND, Term, ID, T, F, label_reset

basics = [ID, T, F, church.Nat(2), ID()(ID), ID().sup(ID())]

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

    self._assert_fmt(church.Nat(0), "λ λa a")
    self._assert_fmt(church.Nat(1), "λa λb ( a b)")
    self._assert_fmt(church.Nat(2), "λa λb ( a ( a b))", hide_dups = True)
    label_reset()
    self._assert_fmt(church.Nat(2), "λa λb ( c where &72{c, d} = a ( d b))", hide_dups = False)
  
  def _assert_run(self, term:Any, expected:str, **envs):
    self._assert_fmt(term.run(), expected, **envs)

  def test_clone(self):
    for term in basics:
      t = Term(term)
      self.assertEqual(str(t), str(t.clone()))

    c2 = Term(church.Nat(2))
    c2c = c2.clone()
    c2string = str(c2)
    wire(c2.srcs[0].port.other(), Port(Node(Tag.Null)))
    self.assertNotEqual(str(c2), c2string)
    assert str(c2c) == c2string
    
  def test_run(self):
    t = ID()(ID())
    res = t.run()
    self._assert_fmt(res, ID())

    self._assert_run(Term.sup(1,2,0)(3), '&0{ ( 1 3) ( 2 3)}')

    self._assert_run(
      church.Nat(2)(church.Nat(2)),
      church.Nat(4),
      hide_dups = True
    )

    self._assert_run(
      church.Suc(church.Nat(2)),
      church.Nat(3),
      hide_dups = True
    )

  def test_scott(self):
    self._assert_run(
      scott.inc()(scott.nat(2)),
      scott.nat(3),
      hide_dups = True
    )

    self._assert_run(
      scott.dec()(scott.nat(2)),
      scott.nat(1),
      hide_dups = True
    )

    self._assert_run(
      scott.to_z()(scott.nat(2)),
      scott.nat(0),
      hide_dups = True
    )


  
  def test_circular(self):

    for i in range(2):
      for j in range(2):

        s = Node(Tag.Sup)
        d = Node(Tag.Dup)
        n = Node(Tag.Null)

        wire((s, PN.MAIN),(d, PN.MAIN))
        wire((s, PN(1 + i)),(d, PN(1 + j)))
        wire((n, PN.MAIN),(s, PN(2 - i)))

        t = Term(Port(d, PN(2 - j)))

        with Context(hide_dups = True): self._assert_fmt(t, Term(None))
        self._assert_run(t, Term(None))

  def compare_backend(self, *term:Any):
    for t in term:
      t = Term(t)
      with BACKEND("python_simple") :
        r1 = t.run()
      with BACKEND("clang"):
        r2 = t.run()
      with print_tree(False):
        if str(r1) != str(r2):
          print(f"ERORR executing {t}")
          print(f"python_simple: {r1}")
          print(f"clang: {r2}")
          raise AssertionError("Error executing term")

  def test_backend(self):
    self.compare_backend(
      ID()(ID()),
      Term(lambda x: x)(lambda y: y),
      Term(lambda x,y: x)(lambda x:x),
      Term(lambda x,y: y)(lambda x:x),
      Term(lambda x: (Term(lambda y:y)(x))),
      Term(lambda x: (Term(lambda x,y:y)(x))),
    )

  def test_backend_app_sup(self):
    s = Term(lambda x,y,z:
      (Term.sup(x,y, 0))(z)
    )
    self.compare_backend(s)
  
  def test_backend_dup_sup(self):
    s = Term.sup(Term(lambda x:x), Term(None),0)
    self.compare_backend(s.dups(0)[0])
    self.compare_backend(s.dups(1)[0])
    self.compare_backend(s.dups(0)[1])
    self.compare_backend(s.dups(1)[1])
  
  def test_backend_lam_dup(self):
    self.compare_backend(Term(lambda x:x).dups(0)[0])
    self.compare_backend(Term(lambda x,y:x).dups(0)[0])


  def test_backend_bigger(self):
    with BACKEND("clang"):
      self.test_scott()

  
    

if __name__ == "__main__":
  unittest.main()