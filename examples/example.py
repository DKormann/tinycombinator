from tinycombinator import IC, execute



c = IC(lambda x: x)(lambda y: y)

d = c.run()



print(c)
print(d)


