#include <stdatomic.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>

typedef int32_t LOC;
typedef int32_t PORT;

typedef struct BST {
  LOC data;
  struct BST *left, *right;
} BST;

BST* insert(BST *root, LOC data) {
  if (!root) {
    BST *n = malloc(sizeof(BST));
    n->data = data; n->left = n->right = NULL;
    return n;
  }
  if (data < root->data) root->left = insert(root->left, data);
  else if (data > root->data) root->right = insert(root->right, data);
  return root;
}

int contains(BST *root, LOC data) {
  if (!root) return 0;
  if (data == root->data) return 1;
  if (data < root->data) return contains(root->left, data);
  return contains(root->right, data);
}

void free_tree(BST *root) {
  if (root) {
    free_tree(root->left);
    free_tree(root->right);
    free(root);
  }
}

#define MAX_TERMS 1<<20
#define RED     "\x1b[31m"
#define RESET   "\x1b[0m"

void error(char* msg){
  printf(RED "fatal: %s\n" RESET, msg );
  exit(1);
}

void assert(int cond, char* msg){
  if (!cond) error(msg);
}


int DEBUG = 0;

void set_debug(int debug){ DEBUG = debug; }

typedef enum{
  App, Lam, Dup, Sup, Null, Prim, ERA, ROOT, Freed
} Tag;


typedef int32_t PORT;

typedef struct Term{
  Tag tag;
  int label;
  PORT s[2];
} Term;

typedef struct {
  PORT root;
  Term stack[MAX_TERMS];
  PORT free_list;
  PORT empty;
  int node_ctr;
  int steps;
  int fuel;
} Runtime;

PORT new_port(LOC loc, int side){
  return loc << 1 | side;
}

int get_loc(PORT port){
  return (port >> 1);
}

int get_side(PORT port){
  return port & 1;
}

int to_s1(PORT port){
  return port | 1;
}

int to_s0(PORT port){
  return (port | 1) ^ 1;
}

Term* get_term(PORT port, Runtime* rt){
  return &rt->stack[get_loc(port)];
}

PORT* get_s(PORT port, Runtime* rt){
  return get_term(port, rt)->s;
}

Tag get_tag(PORT port, Runtime* rt){
  return get_term(port, rt)->tag;
}

int get_label(PORT port, Runtime* rt){
  return get_term(port, rt)->label;
}

void set_tag(PORT port, Tag tag, Runtime* rt){
  get_term(port, rt)->tag = tag;
}

void set_label(PORT port, int label, Runtime* rt){
  get_term(port, rt)->label = label;
}

char* tag_fmt(Tag tag){
  switch (tag){
    case App: return "App";
    case Lam: return "Lam";
    case Dup: return "Dup";
    case Sup: return "Sup";
    case Null: return "Null";
    case Prim: return "Prim";
    case ERA: return "ERA";
    case ROOT: return "ROOT";
    case Freed: return "Freed";
  }
}

char* term_fmt(PORT port, Runtime* rt){
  Term* term = get_term(port, rt);

  char*buf = malloc(sizeof(char) * 100);

  int l1 = get_loc(term->s[0]);
  int l2 = get_loc(term->s[1]);
  int s1 = get_side(term->s[0]);
  int s2 = get_side(term->s[1]);
  
  switch (get_tag(port, rt)){
    case Dup:
      snprintf(buf, 100, "Dup%d: <%d,%d> <xor= %d,%d>", get_label(port, rt) , l1, s1, l2, s2); break;
    case Sup:
      snprintf(buf, 100, "Sup%d: <%d,%d> <%d,%d>", get_label(port, rt) , l1, s1, l2, s2); break;
    case ERA: case ROOT: case Null:
      snprintf(buf, 100, "%s: <%d,%d>", tag_fmt(get_tag(port, rt)), l1, s1); break;
    default:
      snprintf(buf, 100, "%s: <%d,%d> <%d,%d>", tag_fmt(term->tag), l1, s1, l2, s2); break;
  }
  return buf;
}



char* port_fmt(PORT port, Runtime* rt){
  char* buf = malloc(sizeof(char) * 100);
  char* tf = term_fmt(port, rt);
  snprintf(buf, 100, "<%d,%d: %s>", get_loc(port), get_side(port), tf);
  return buf;
}


void _tree(PORT port, int d, BST* seen, Runtime* rt){

  int loc = get_loc(port);
  Tag tag = get_tag(port, rt);
  char* stag = tag_fmt(tag);
  if (loc < 10) printf(" "); if (loc < 100) printf(" ");
  printf("%d:", loc);
  for (int i = 0; i < d; i++) printf("  ");

  if (contains(seen, port)){ printf("%s,%d <-\n", stag, port & 1); return;}
  seen = insert(seen,port);
  
  PORT* src = get_s(port, rt);
  
  switch (tag){
    case Lam:
      if (get_side(port) == 1)printf("Var\n");
      else{

        printf("Lam -> %d,%d %s\n", get_loc(src[0]), src[0] & 1, tag_fmt(get_tag(src[0], rt)));
        _tree(src[1], d+1, seen, rt);}
      break;
    case Null: case ERA: case Freed: case Prim:
      printf("%s\n", stag);break;
    case ROOT:
      printf("Root\n");
      _tree(src[0], d+1, seen, rt);
      break;
    case Dup:{
      printf("Dup%d %d xor%d %d\n", get_label(port, rt), get_side(port), src[1] >> 1, src[1] & 1);
      _tree(src[0], d+1, seen, rt);
      break;
    }
    case Sup:{
      printf("Sup%d\n", get_label(port, rt));
      _tree(src[0], d+1, seen, rt);
      _tree(src[1], d+1, seen, rt);
      break;
    }
    case App:
      printf("%s\n", stag);
      _tree(src[0], d+1, seen, rt);
      _tree(src[1], d+1, seen, rt);
      break;
  }
}

void tree(Runtime* rt){_tree(rt->root, 0, NULL, rt);}

Runtime* new_runtime(){
  Runtime* rt = calloc(1, sizeof(Runtime));
  return rt;
}

void set_root(LOC root, Runtime* rt){
  rt->root = root;
}

LOC get_root(Runtime* rt){
  return rt->root;
}


void set_port(PORT port, PORT content, Runtime* rt){
  printf("set port %d %d %d %d\n", port>>1, port & 1, content>>1, content & 1);
  get_s(port, rt)[get_side(port)] = content;
}

PORT get_port(PORT port, Runtime* rt){
  Term node = rt->stack[get_loc(port)];
  if (node.tag == Dup) return node.s[0];
  return node.s[port & 1];
}


void set_dup_aux(PORT port, PORT a, PORT b, Runtime* rt){
  printf("set dup aux %s\n", port_fmt(port, rt));
  Tag duptag = get_tag(port, rt);
  if (duptag != Dup) printf("cannot set aux ports of non-dup %s\n", tag_fmt(port));
  get_s(port, rt)[1] = a ^ b;
  printf("set dup aux %d\n", get_s(port, rt)[1] >> 1);
}

void get_dup_aux(PORT* owner, PORT* b, Runtime* rt){
  PORT dup = get_port(*owner, rt);
  PORT xd = get_s(dup, rt)[1];
  if ((dup & 1)) (*owner) ^= xd;
  *b = xd ^ *owner;
}

PORT new_node(Tag tag, int label, Runtime* rt){

  PORT port = 0;
  if (rt->free_list != 0){
    port = rt->free_list;
    port = (port>>1) << 1;
    rt->free_list = get_port(port, rt);
  }else{
    port = rt->empty;
    rt->empty = new_port(get_loc(rt->empty) + 1, 0);
    if (get_loc(rt->empty) >= MAX_TERMS) error("Error: MAX_TERMS reached\n");
  }
  rt->node_ctr ++;
  set_tag(port, tag, rt);
  set_label(port, label, rt);
  get_s(port, rt)[0] = 0;
  get_s(port, rt)[1] = 0;

  return port;
}

void free_node(PORT port, Runtime* rt){
  if (get_tag(port, rt) == Freed){
    printf(RED "Error: Term %s is already freed\n", term_fmt(port, rt));
    exit(1);
  }
  set_tag(port, Freed, rt);
  set_port(port, rt->free_list, rt);
  rt->free_list = port;
}



void _check(PORT owner, BST* seen,Runtime* rt){
  PORT port = get_port(owner, rt);
  Term* term = get_term(port, rt);

  if (contains(seen, port)) return;
  seen = insert(seen, port);

  switch (term->tag){
    case Lam:{

      int bindrloc = term->s[0] >> 1;
      if (get_side(port) == 1){
        int ownerloc = get_loc(owner);
        if (bindrloc != ownerloc){
          tree(rt);
          printf(RED);
          printf("ERR lam doesnt point to var OWNER:%s\n", port_fmt(owner, rt));
          printf("port: %s\n", port_fmt(port, rt));
          printf(RESET);
          exit(1);
        }
      }
      
      if (get_tag(term->s[0], rt) != ERA){
        int bindr = term->s[0];
        if (get_port(bindr, rt) >> 1 != port >> 1){
          tree(rt);
          printf(RED);
          printf("ERR var doesnt point to lam OWNER:%s\n", port_fmt(owner, rt));
          printf(RESET);
          exit(1);
        }
      }
      _check(port | 1, seen, rt);
      break;
    }

    case Dup:{
      PORT other = term->s[1] ^ owner;

      if (get_term(other, rt)->tag != ERA && get_port(other, rt) >> 1 != port >> 1){
        tree(rt);
        printf("owner: %s\n", port_fmt(owner, rt));
        printf(RED "DUP ERROR: %s\n" RESET, port_fmt(port, rt));
        printf("owner: %s\n", port_fmt(owner, rt));
        printf("other: %s\n", port_fmt(other, rt));
        exit(1);
      }
      _check((port >> 1 << 1) | 0 , seen, rt);
      break;
    }

    case Sup: case App:{
      _check(port ^ 0, seen, rt);
      _check(port ^ 1, seen, rt);
      break;
    }
    // default: break;
    case Null: break;
    case ERA: break;
    case ROOT: break;
    case Prim: break;
    case Freed:
      // error("Freed term found");
      tree(rt);
      printf(RED "Freed term found: %s\n" RESET, port_fmt(port, rt));
      exit(1);
      
    }

}

void check_term(Runtime* rt){
  BST* seen = insert(NULL, -1);
  _check(rt->root, seen, rt);
}

void erase(PORT owner, Runtime* rt){
  PORT port = get_port(owner, rt);

  printf("erase %d,%d -> %s\n", owner >> 1, owner &1, port_fmt(port, rt));
  switch (get_tag(port, rt)){

    case Lam:{
      set_port(get_s(port, rt)[0], new_node(ERA, 0, rt), rt);
      printf("ERAS BOD\n");
      erase(to_s1(port), rt);
      break;
    }
    case Dup:{
      PORT * dup_s = get_s(port, rt);
      PORT other = dup_s[1] ^ owner;
      if (get_tag(other, rt) == ERA){
        printf("owner: %s\n", port_fmt(owner, rt));
        printf("other: %s\n", port_fmt(other, rt));
        printf("ERASE FULL DUP\n");

        erase(dup_s[0], rt);
        free_node(port, rt);
      }else{
        PORT era = new_node(ERA, 0, rt);
        printf("era: %s\n", port_fmt(era, rt));
        dup_s[1] = other ^ era;
        printf("ERASE DUP AUX owner: %s other: %s\n", port_fmt(owner, rt), port_fmt(other, rt));
        printf("dup_s[1]: %d %d\n", dup_s[1] >> 1, dup_s[1] & 1);
      }
      break;
    }
    case Sup:{

      erase(get_s(port, rt)[0], rt);
      erase(get_s(port, rt)[1], rt);
      break;
    }
    default: break;
  }

}

void move(PORT port, PORT owner, Runtime* rt){


  PORT content = get_port(owner, rt);
  Term* tar = get_term(content,rt);

  if (get_tag(port, rt) == ERA) {
    printf("lets erase %s\n", port_fmt(owner, rt));
    erase(owner, rt);
    return;
  }
  if (tar->tag == Lam && get_side(content) == 1) tar->s[0] = port;
  if (tar->tag == Dup) {
    printf("DUP update\n");
    tar->s[1] ^= owner ^ port;}
  set_port(port, content, rt);

}

void app_lam(PORT owner, PORT app, PORT lam, Runtime* rt){
  PORT var = get_s(lam, rt)[0];
  PORT arg = get_port(app | 1, rt);
  printf("arg: %d\n", (get_term(arg,rt)->s[1]) >> 1);
  // printf("app_lam var: %s arg: %s\n", port_fmt(var, rt), port_fmt(arg, rt));
  move(var, app | 1, rt);
  move(owner, lam | 1, rt);
}



PORT mk_dup(PORT a, PORT b, PORT owner, int label, Runtime* rt){
  PORT dup = new_node(Dup, label, rt);
  set_dup_aux(dup, a, b, rt);
  set_port(a, new_port(get_loc(dup), 0), rt);
  set_port(b, new_port(get_loc(dup), 1), rt);

  

  move(dup, owner, rt);
  return new_port(get_loc(dup), 0);
}


void app_sup(PORT owner, PORT app, PORT sup, Runtime* rt){


  printf("app_sup %s\n", port_fmt(owner, rt));
  PORT app1 = new_node(App, 0, rt);
  PORT app2 = new_node(App, 0, rt);

  printf("app1: %s\n", port_fmt(app1, rt));

  move(app1 | 0, sup | 0, rt);
  move(app2 | 0, sup | 1, rt);

  mk_dup(
    app1 | 1,
    app2 | 1,
    new_port(get_loc(app), 1),
    get_label(sup, rt),rt);

  
  PORT sres = new_node(Sup, get_label(sup, rt), rt);

  set_port(new_port(get_loc(sres), 0), app1, rt);
  set_port(new_port(get_loc(sres), 1), app2, rt);
  set_port(owner, sres, rt);

}

void app_null(PORT owner, PORT app, PORT null, Runtime* rt){
  erase(owner, rt);
  set_port(owner, null, rt);
}


void dup_sup(PORT owner, PORT dup, PORT sup, Runtime* rt){
  int dlab = get_label(dup, rt);
  int slab = get_label(sup, rt);

  printf("owner: %s\n", port_fmt(owner, rt));

  PORT other;
  get_dup_aux(&owner, &other, rt);

  if (dlab == slab){
    printf("DUP SUP SAME LABEL\n");

    printf("owner: %s\n", port_fmt(owner, rt));
    printf("other: %s\n", port_fmt(other, rt));

    move(owner, sup | 0, rt);
    move(other, sup | 1, rt);

  }else{
    PORT S1 = new_node(Sup, slab, rt);
    PORT S2 = new_node(Sup, slab, rt);

    mk_dup(S1 | 0, S2 | 0, (get_loc(sup) << 1) | 0, dlab, rt);
    mk_dup(S1 | 1, S2 | 1, (get_loc(sup) << 1) | 1, dlab, rt);

    set_port(owner, S1, rt);
    set_port(other, S2, rt);
  }
}

void set_var(PORT target, PORT lam, Runtime* rt){
  set_port(target, lam | 1, rt);
  set_port(lam | 0, target, rt);
}


void erase_lam(PORT lam, Runtime* rt){
  // set_port(to_s0(lam), new_node(Null, 0, rt), rt);

  PORT var = get_s(lam, rt)[0];
  printf("var: %s\n", port_fmt(var, rt));
  set_port(var, new_node(Null, 0, rt), rt);
  erase(to_s1(lam), rt);
}

void dup_lam(PORT owner, PORT dup, PORT lam, Runtime* rt){
  int lab = get_label(dup, rt);
  PORT other;
  get_dup_aux(&owner, &other, rt);

  Term* lam_term = get_term(lam, rt);

  PORT L2 = new_node(Lam, 0, rt);
  PORT L1 = new_node(Lam, 0, rt);

  PORT bod = lam_term->s[1];


  PORT DUP = mk_dup(L1 | 1, L2 | 1, lam | 1, lab, rt);

  if (get_tag(lam_term->s[0], rt) == ERA){

    set_port(L1 | 0, new_node(ERA, 0, rt), rt);
    set_port(L2 | 0, new_node(ERA, 0, rt), rt);

  }else{

    PORT varsup = new_node(Sup, lab, rt);
    
    set_port(lam_term->s[0], varsup, rt);
    
    set_var(varsup | 0, L1, rt);
    set_var(varsup | 1, L2, rt);
  }

  printf("L1: %s\n", port_fmt(L1, rt));
  printf("L2: %s\n", port_fmt(L2, rt));


  if (get_tag(owner, rt) == ERA) {
    printf("lets erase L1\n");
    erase_lam(L1, rt);
  }
  else set_port(owner, L1, rt);

  if (get_tag(other, rt) == ERA) {
    printf("lets erase L2\n");
    erase_lam(L2, rt);
  }
  else set_port(other, L2, rt);


  printf("owner: %s\n", port_fmt(owner, rt));
  printf("other: %s\n", port_fmt(other, rt));
}

void dup_null(PORT owner, PORT dup, PORT null, Runtime* rt){
  PORT other = get_s(dup, rt)[1] ^ owner;
  set_port(other, null, rt);
  set_port(owner, new_node(Null, 0, rt), rt);
}

int handle_redex(PORT owner, PORT term, Runtime* rt){
  if (get_port(owner, rt) != term) error("owner and term do not match");

  if (rt->steps >= rt->fuel) return 0;
  Tag tag = get_tag(term, rt);
  PORT other = get_s(term, rt)[0];
  Tag otag = get_tag(other, rt);
  if (otag == Lam && get_side(other) == 1) return 0;

  void(*handler)(PORT, PORT, PORT, Runtime*) = 
    (tag == App) ?
      ( otag == Lam ? app_lam
      : otag == Sup ? app_sup
      : otag == Null ? app_null
      : NULL)
    :(tag == Dup) ?
      ( otag == Lam ? dup_lam
      : otag == Sup ? dup_sup
      : otag == Null ? dup_null
      : NULL) : NULL;

  if (handler != NULL){
    if (DEBUG) printf("REDEX:%d %d %s <> %s \n", owner >> 1, term>>1, tag_fmt(tag), tag_fmt(otag));
    handler(owner, term, other, rt);

    rt->steps ++;
    check_term(rt);
    return 1;
  }
  return 0;
}

int step(PORT owner, BST* seen, Runtime* rt){

  // printf("step %s\n", port_fmt(owner, rt));

  if (contains(seen, owner)){

    return 0;
  }
  insert(seen, owner);
  PORT term = get_port(owner, rt);

  if (handle_redex(owner, term, rt)){
    printf("SUCC\n");
    return 1;
  }

  switch (get_tag(term, rt)){
    case App:  case Sup:{
      return step(term ^ 0, seen, rt) || step(term ^ 1, seen, rt);
    }
    case Dup:{
      return step((term >> 1 << 1), seen, rt);
    }
    case Lam:{
      return step((term >> 1 << 1) | 1, seen, rt);
    }
    case ROOT:{
      return step(term, seen, rt);
    }
    default: return 0;
  }
}

void reduce(PORT term, BST* seen, Runtime* rt){
  while (step(term, insert(NULL, -1), rt)){
    tree(rt);

  }
}

int run(Runtime* rt, int steps){
  rt->fuel = steps;
  rt->steps = 0;

  PORT root = rt->root;
  BST* ctx = insert(NULL, -1);
  if (DEBUG) tree(rt);
  check_term(rt);
  reduce(root, ctx, rt);
  return rt->steps;   
}