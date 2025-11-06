
import subprocess, ctypes, os, hashlib, threading
import time
import sys
from typing import Callable, Dict, Set

# from tinycombinator.run import reduce
from tinycombinator.ast import IC, ast_main

ast_main()
# from tinycombinator.helpers import BACKEND, DEBUG, TIMEIT, hide_dups


# tmp_path = os.path.join( os.path.dirname(__file__), "../.tmp")

# os.makedirs(tmp_path, exist_ok=True)

# so_path = os.path.join(tmp_path, "main.so")
# c_cache_path = os.path.join(tmp_path, "c_hash")
# main_path = os.path.join(os.path.dirname(__file__), "main.c")


# with open(main_path, "rb") as f: c_hash = hashlib.md5(f.read()).hexdigest()

# def compile_c():
#   with open(c_cache_path, "w") as f: f.write(c_hash)
#   print("Compiling...")
#   os.makedirs(tmp_path, exist_ok=True)
#   subprocess.check_call(["clang", "-shared", "-O0", "-fPIC", main_path, "-o", so_path])

# if not os.path.exists(c_cache_path): compile_c()
# else:
#   with open(c_cache_path, "r") as f:
#     if f.read().strip() != c_hash: compile_c()

# _local = threading.local()

# def get_lib():
#   if not hasattr(_local, 'lib'):
#     _local.lib = ctypes.CDLL(so_path)
#     def go(name, inp, out):
#       try:
#         getattr(_local.lib, name).argtypes = inp
#         getattr(_local.lib, name).restype = out
#       except Exception as e:
#         print(f"Error loading lib {name}: {e}")
#         exit(1)
#     go("new_runtime", [], ctypes.c_void_p)
#     go("get_root", [ctypes.c_void_p], ctypes.c_int)
#     go("get_ic", [ctypes.c_int, ctypes.c_void_p], ctypes.c_void_p)
#     go("get_tag", [ctypes.c_int, ctypes.c_void_p], ctypes.c_int)
#     go("port_side", [ctypes.c_int, ctypes.c_int, ctypes.c_void_p], ctypes.c_int)
#     go("port_target", [ctypes.c_int, ctypes.c_int, ctypes.c_void_p], ctypes.c_int)
  


#     # go("get_tag", [ctypes.c_void_p], ctypes.c_int)
#     # go("get_label", [ctypes.c_void_p], ctypes.c_int)
#     # go("port_info", [ctypes.c_void_p, ctypes.c_int, ctypes.c_int], ctypes.c_void_p)
#     # go("set_port", [ctypes.c_void_p, ctypes.c_int, ctypes.c_void_p], None)
#     # go("empty_IC", [ctypes.c_int, ctypes.c_int, ctypes.c_void_p], ctypes.c_void_p)
#     # go("set_auxs", [ctypes.c_void_p, ctypes.c_void_p, ctypes.c_void_p], None)
#     # go("set_debug", [ctypes.c_int], None)
#     go("run", [ctypes.c_int, ctypes.c_void_p], ctypes.c_int)

#     _local.lib.set_debug(DEBUG.get())
  
#   _local.lib.set_debug(DEBUG.get())

#   return _local.lib


# def load_term_c(term: IC)->ctypes.c_void_p:
#   lib = get_lib()
#   nodes = dict[IC, ctypes.c_void_p]()
#   runtime = lib.new_runtime()
#   def visit(node: IC):
#     if node in nodes: return
#     if node is None or node.tag == Tag.Var: return
#     nodes[node] = get_lib().empty_IC(node.tag.value - 1, node.label if node.label is not None else 0, runtime)
#     visit(node.s[0])
#     visit(node.s[1])
#   visit(term)
#   for node in nodes:
#     if node is None: continue
#     for side in range(2):
#       chd = node.s[side]
#       if chd:
#         if chd.tag == Tag.Var:
#           if side == 0 or chd.s[0] is not node:
#             lib.set_port(nodes[chd.s[0]], 1, lib.port_info(nodes[node], side, 1))
#             lib.set_port(nodes[node], side, lib.port_info(nodes[chd.s[0]], 1, 1))
#         else: lib.set_port(nodes[node], side, nodes[chd])
#   lib.set_root(nodes[term], runtime)
#   return runtime



# all_tags = list(Tag.__members__.values())

# # def unload_term_c(runtime)->IC:
# #   lib = get_lib()
# #   nodes: Dict[ctypes.c_void_p, IC] = {}
# #   nodes[None] = None
# #   subst : Dict[ctypes.c_void_p, IC] = {}

# #   def get_var(loc: ctypes.c_void_p)->IC:
# #     if loc not in subst: subst[loc] = IC(Tag.Freed)
# #     else: subst[loc].tag = Tag.Var
# #     return subst[loc]

# #   def visit(node: ctypes.c_void_p):

# #     print(node, lib.port_info(node, 1, 0))
# #     if node not in nodes:
# #       tag = all_tags[lib.get_tag(node)]
# #       nodes[node] = IC(tag, label = lib.get_label(node))
# #       s0 = lib.port_info(node, 0, 0)
# #       if s0 is None: s0 = get_var(lib.port_info(node, 0, 1))
# #       else: s0 = visit(s0)
      
# #       nodes[node].s[0] = s0
# #       s1 = lib.port_info(node, 1, 0)
# #       if s1 is not None and tag == Tag.Lam:
# #         loc = lib.port_info(node, 1, 0)
# #         s1 = get_var(loc)
# #         s1.s[0] = nodes[node]
# #       else:
# #         s1 = lib.port_info(node, 1, 0)
# #         loc = lib.port_info(node, 1, 1)
# #         if s1 is None: s1 = get_var(loc)
# #         else: s1 = visit(s1)

# #       nodes[node].s[1] = s1
# #     return nodes[node]
  
# #   res = visit(lib.get_root(runtime))
  
# #   for node in nodes.values():
# #     if node and node.s[0].tag == Tag.Freed: node.s[0] = None
# #     if node and node.s[1].tag == Tag.Freed: node.s[1] = None
  
# #   return res


# def unload_term_c(runtime: ctypes.c_void_p)->IC:
#   lib = get_lib()

#   print(f"{runtime = :x}")
#   root = lib.get_ic(lib.get_root(runtime), runtime)
#   print(f"{root=:x}")
#   print(f"{lib.get_tag(0, runtime) = :x}")
#   print(f"{lib.port_side(0, 0, runtime) = :x}")
#   print(f"{lib.port_target(0, 0, runtime) = :x}")
#   print(f"{lib.port_side(0, 1, runtime) = :x}")
#   print(f"{lib.port_target(0, 1, runtime) = :x}")


  

# DEFAULT_FUEL = 1<<30
# def run(runtime, steps:int = DEFAULT_FUEL): return get_lib().run(steps, runtime)

# def get_node_count_c() -> int: return get_lib().get_node_count()

# def run_term_c(term:IC, maxsteps: int = DEFAULT_FUEL, runs = DEFAULT_FUEL) -> IC:

#   t = 0

#   if DEBUG: print(term)
#   for batch in range(runs):
#     runtime = load_term_c(term)
#     st = time.time_ns()
#     steps = run(runtime, int(maxsteps))
#     t += time.time_ns() - st
#     term = unload_term_c(runtime)
#     sys.stdout.flush()
#     if DEBUG: print(term)
#     if steps < maxsteps: break
#   if TIMEIT:
#     total_steps = batch * maxsteps + steps
#     print(f"\n{total_steps} steps: {t/1e9} seconds {(total_steps)/(t+1e-9)*1e3:.3f} Mips")
#   if DEBUG:
#     with hide_dups(True): print(term)
#   return term


def execute(node:IC, *args, **kwargs)->Callable[[IC, int, int], IC]:
  pass
#   if BACKEND == "c": return run_term_c(node, *args, **kwargs)
#   if BACKEND == "py": return reduce(node.copy())
#   raise ValueError(f"Invalid backend: {BACKEND}")






# if __name__ == "__main__":

#   ast_main()

#   # rt = get_lib().new_runtime()
#   # get_lib().run(1, rt)  
#   # unload_term_c(rt)



#   # term = IC(lambda x:x)

#   # rt = load_term_c(term)

#   # res = unload_term_c(rt)
#   # print(res)


#   # # term = IC(lambda x,y: x) (lambda z:z)
#   # # term = term.run()

#   # # # assert str(term) == "λ λa a"
#   # # print(term)

#   # # # term = IC(lambda x:x)
#   # # # ds = dup(term)
#   # # # print(ds[0])

#   # # # rt = load_term_c(ds[0])

#   # # # run(rt, 1)

#   # # # term = unload_term_c(rt)

#   # # # print(term)



