from tinycombinator import Node, execute



c = Node(lambda x: x)(lambda y: y)

d = c.run()



print(c)
print(d)


