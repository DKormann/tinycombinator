from typing import Any
import unittest


from tinycombinator.helpers import Context, Env, hide_dups, print_tree
from tinycombinator.lib import church, scott
from tinycombinator.nodes import MathOps, Node, Port, Tag, wire, PN
from tinycombinator.term import BACKEND, Term, ID, T, F, label_reset

sup_ex = Term.sup(Term(lambda x:x), Term(None),0)



basics = [ID, T, F, church.Nat(2), ID()(ID), ID().sup(ID())]

class ConstructionRepresentation(unittest.TestCase):

  def _assert_fmt(self, term:Any, expected:str, **envs):
    with print_tree(False), Context(**envs):
      if isinstance(expected, Term): expected = str(expected)
      if callable(expected): expected = str(Term(expected))
      if not isinstance(expected, str): expected = str(expected)

      self.assertEqual(str(Term(term)), expected)
  
  def test_fmt(self):
    self._assert_fmt(ID, "λa a")
    self._assert_fmt(ID(), "λa a")
    self._assert_fmt(T, "λa λ a")
    self._assert_fmt(T(), "λa λ a")
    self._assert_fmt(F, "λ λa a")
    self._assert_fmt(sup_ex.dups(0)[0], "a where &0{a, b} = &0{ λc c NULL}")
    self._assert_fmt(sup_ex.dups(0)[1], "b where &0{a, b} = &0{ λc c NULL}")
    self._assert_fmt(sup_ex.dups(1)[0], "a where &1{a, b} = &0{ λc c NULL}")
    self._assert_fmt(church.Nat(0), "λ λa a")
    self._assert_fmt(church.Nat(1), "λa λb ( a b)")
    self._assert_fmt(church.Nat(2), "λa λb ( a ( a b))", hide_dups = True)
    label_reset()
    self._assert_fmt(church.Nat(2), "λa λb ( d where &72{c, d} = a ( c b))", hide_dups = False)
  
  def _assert_run(self, term:Any, expected:str, **envs):

    self._assert_fmt(Term(term).run(), expected, **envs)

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

    self._assert_run(ID()(ID()), ID())

    self._assert_run(sup_ex.dups(0)[0], "λa a")
    self._assert_run(sup_ex.dups(0)[1], "NULL")
    self._assert_run(sup_ex.dups(1)[0], "&0{ λa a NULL}")

    self._assert_run(Term(lambda x,y:x).dups(0)[0], Term(lambda x,y:x))
    self._assert_run(Term(lambda x,y:y).dups(0)[0], Term(lambda x,y:y))
    self._assert_run(Term(lambda x,y:y).dups(0)[0].dups(1)[1], Term(lambda x,y:y))

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

    self._assert_run(Term(lambda x,y: x)(lambda x:x), lambda x,y:y)
    self._assert_run(Term(lambda x: (Term(lambda y:y)(x))), lambda x:x)
    self._assert_run(Term(lambda x: (Term(lambda x,y:y)(x))), lambda x,y:y)
    self._assert_run(Term(lambda x,y,z:(Term.sup(x,y, 0))(z)), "λa λb λc &0{ ( a d where &0{d, e} = c) ( b e)}")

  def test_primitives(self):

    self._assert_run(lambda x,y: Term.sup(x,y,0)(3), 'λa λb &0{ ( a 3) ( b 3)}')
    self._assert_run(Term(1) + 2, 3)
    self._assert_run(Term(1) + (Term(2) + 3), 6)
    self._assert_run(Term(2) - 1, 1)

    for i in [2,5,7]:
      for j in [3,4,6]:
        for op in [MathOps.Add, MathOps.Mul, MathOps.Sub, MathOps.Mod, MathOps.Pow]:
          t = Term(Node(Tag.Prim, value = op))(Term(i), Term(j))
          self._assert_run(t, eval(f"{i} {op} {j}"))
        for op in [MathOps.Eq, MathOps.Ne, MathOps.Lt, MathOps.Gt]:
          t = Term(Node(Tag.Prim, value = op))(Term(i), Term(j))
          self._assert_run(t, T() if  eval(f"{i} {op} {j}") else F())

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
      scott.to_z()(scott.nat(1)),
      scott.nat(0),
      hide_dups = True
    )

    for a in [2,3]:
      for b in [2,3]:
        self._assert_run(
          scott.eq()(scott.nat(a), scott.nat(b)),
          scott.boolean(a==b)
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

  def _test_backend(self, backend:str):
    with BACKEND(backend):
      self.test_fmt()
      self.test_run()
      self.test_circular()
      self.test_primitives()
      self.test_scott()
  
  def test_clang(self):
    self._test_backend("clang")
      


if __name__ == "__main__":
  unittest.main()