


from tinycombinator.ast import IC, Tag, move
from typing import Dict, List


from dataclasses import dataclass


@dataclass
class VariantType:
  type: "Adt"
  name: str

  def __call__(self, *args)-> IC:
    num = [k for k in self.type.variants.keys()].index(self.name)
    bod = None
    lams = []
    for i in range(len(self.type.variants)):
      bod = IC(Tag.Lam, bod)
      lams.append(bod)

    bod = IC(Tag.Var, lams[num])
    lams[-num-1].s1 = bod

    for arg in args: bod = bod(arg)

    lams[0].s0 = bod

    return lams[-1]

  def __repr__(self): return f"{self.name}"


@dataclass
class Adt:

  variants: Dict[str, list]

  def __init__(self, **variants): self.variants = variants
  def __repr__(self): return f"Adt({self.variants})"

  def match(self, **patterns):
    res = IC(lambda x:x)
    for var in self.variants.keys():
      case = patterns[var]
      res.s0 = res.s0(case)
    return res

  def __getattr__(self, name): return VariantType(self, name)


LIST = Adt(nil=[], cons=["head", "tail"])

LIST.cons(0, LIST.nil())




if __name__ == "__main__":
  print(LIST.cons(0, LIST.nil()))
