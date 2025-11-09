
from tinycombinator.helpers import DEBUG, debug
from tinycombinator.ic import Node, IC, Tag



def app_lam(app: Node, lam: Node)->Node:
  loc = lam.s[1]
  if loc is not None: loc.target.s[loc.side] = app.s[1]
  return lam.s[0].target

def app_sup(app: Node, sup: Node)->Node:

  # if app.label == sup.label:

  raise NotImplementedError("app_sup not implemented")


def dup_lam(dup: Node, lam: Node)->Node:
  raise NotImplementedError("dup_lam not implemented")

def dup_sup(dup: Node, sup: Node)->Node:
  raise NotImplementedError("dup_sup not implemented")



def redex(term: Node)->Node:

  handler = None
  if term.s[0] is None: return term
  other = term.s[0].target

  match term.tag:
    case Tag.App:
      match other.tag:
        case Tag.Lam: handler = app_lam
        case Tag.Sup: handler = app_sup
    case Tag.Dup:
      match other.tag:
        case Tag.Lam: handler = dup_lam
        case Tag.Sup: handler = dup_sup
  debug(f'HANDLER: {handler.__name__}')
  if handler is not None: return handler(term, other)

      


def run(term: Node)->Node:
  return redex(term.copy())

def normalize(term: Node)->Node:
  pass


