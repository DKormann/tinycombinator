from tinycombinator import Term



c = Term(lambda x: x)(lambda y: y)

print(c)



print(c.sup(lambda x:x, 1))

r = c.run()

print(r)
