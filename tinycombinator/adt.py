from functools import cached_property
from tinycombinator.ast import IC, Tag
from typing import Dict
from dataclasses import dataclass

@dataclass
class VariantType:
  type: "Adt"
  name: str

  @cached_property
  def index(self)->int: return [k for k in self.type.variants.keys()].index(self.name)

  @cached_property
  def size(self)->int: return len(self.type.variants[self.name])


  def __call__(self, *args)-> IC:
    bod = None
    lams = []
    for _ in range(len(self.type.variants)): lams.append(bod := IC(Tag.Lam, bod))
    bod = IC(Tag.Var, lams[self.index])
    lams[-self.index-1].s1 = bod

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
    for var in self.variants.keys(): res.s0 = res.s0(patterns[var])
    return res
  def __getattr__(self, name): return VariantType(self, name)

LIST = Adt(nil=[], cons=["head", "tail"])
LIST.cons(0, LIST.nil())

if __name__ == "__main__":
  print(LIST.cons(0, LIST.nil()))
