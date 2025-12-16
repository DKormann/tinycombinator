# dscript

a minimal functional language scripting lang

type list = cons a b | nil

let m = cons 1 nil

let p = match m
  (cons(h, t)) 2
  (nil) 0

struct point = {
  x: int,
  y: int
}

let x_1 = (p : point) => match {x} x + 1

map = (f, l) : list => match l
  (cons(h, t)) list.cons f(h) map(f, t) 
  (nil) list.nil





