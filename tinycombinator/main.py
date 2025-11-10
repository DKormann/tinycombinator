

# from tinycombinator.term import ID, Term, step


# if __name__ == "__main__":


#   t = Term(ID)(ID)

#   print(t)
#   print(step(t))


#   t = Term.sup(2, 3, 0)

#   t = t(2)
#   print(t)

#   t = step(t)
#   print(t)

#   t = step(t)


#   print(t)


from tinycombinator.term import ID, T, Term, parse_fun


if __name__ == "__main__":
  t = Term(parse_fun(lambda x, y: y))

  print(t)

