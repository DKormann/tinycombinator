


from tinycombinator.term import ID, Term




app_ids = ID()(ID())

sup_ids = ID().sup(ID())


def churchNat(n:int)->Term:
  def res(s: Term, z: Term)->Term:
    for _ in range(n): z = s(z)
    return z
  return Term(res)


