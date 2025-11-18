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

  char*buf = malloc(sizeof(char) * 20);

  int l1 = get_loc(term->s[0]);
  int l2 = get_loc(term->s[1]);
  int s1 = get_side(term->s[0]);
  int s2 = get_side(term->s[1]);
  
  switch (get_tag(port, rt)){

    case Dup:
      sprintf(buf, "%s%d: <%d %d> <xor= %d %d>", tag_fmt(get_tag(port, rt)), get_label(port, rt) , l1, s1, l2, s2); break;
    case Sup:
      sprintf(buf, "%s%d: <%d %d> <%d %d>", tag_fmt(get_tag(port, rt)), get_label(port, rt) , l1, s1, l2, s2); break;
    case ERA: case ROOT: case Null:
      sprintf(buf, "%s: <%d %d>", tag_fmt(get_tag(port, rt)), l1, s1); break;
    default:
      sprintf(buf, "%s: <%d %d> <%d %d>", tag_fmt(term->tag), l1, s1, l2, s2); break;
  }
  return buf;
}


void _tree(PORT port, int d, BST* seen, Runtime* rt){


  int loc = get_loc(port);
  Tag tag = get_tag(port, rt);
  char* stag = tag_fmt(tag);
  if (loc < 10) printf(" "); if (loc < 100) printf(" ");
  printf("%d:", loc);
  for (int i = 0; i < d; i++) printf("  ");

  if (contains(seen, port)){ printf("%s <-\n", stag); return;}
  seen = insert(seen,port);
  
  PORT* src = get_s(port, rt);
  
  switch (tag){


    case Lam:
      if (get_side(port) == 1)printf("Var\n");
      else{printf("Lam\n"); _tree(src[1], d+1, seen, rt);}
      break;
    case Null: case ERA: case Freed: case Prim:
      printf("%s\n", stag);break;
    case ROOT:
      printf("Root\n");
      _tree(src[0], d+1, seen, rt);
      break;
    case Dup:{
      printf("Dup%d %d\n", get_label(port, rt), get_side(port));
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
      printf("%s %d\n", stag, loc);
      _tree(src[0], d+1, seen, rt);
      _tree(src[1], d+1, seen, rt);
      break;
  }
}

void tree(Runtime* rt){_tree(rt->root, 0, NULL, rt);}

char* port_fmt(PORT port, Runtime* rt){
  char* buf = malloc(sizeof(char) * 20);
  char* tf = term_fmt(port, rt);
  sprintf(buf, "%d:<%d %s>", get_loc(port), get_side(port), tf);
  return buf;
}






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

void error(char* content){
  fprintf(stderr, RED "Error: %s\n" RESET, content);
  exit(1);
}

void set_port(PORT port, PORT content, Runtime* rt){


  get_s(port, rt)[get_side(port)] = content;
}

PORT get_port(PORT port, Runtime* rt){
  return rt->stack[get_loc(port)].s[get_side(port)];
}

void set_dup_aux(PORT port, PORT a, PORT b, Runtime* rt){
  Tag duptag = get_tag(port, rt);
  if (duptag != Dup) printf("cannot set aux ports of non-dup %s\n", tag_fmt(port));
  get_s(port, rt)[1] = a ^ b;
}

void get_dup_aux(PORT* owner, PORT* b, Runtime* rt){
  PORT dup = get_port(*owner, rt);
  PORT xd = get_s(dup, rt)[1];
  *b = xd ^ *owner;
  if ((dup & 1) == 1){
    printf("SAWP\n");
    PORT tmp = *owner;
    *owner = *b;
    *b = tmp;
  }
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
  if (get_tag(port, rt) == Dup && get_side(owner) == 0){
    // this could be a var pointing to dup main
    return;
  }

  if (contains(seen, port)) return;
  seen = insert(seen, port);
  switch (get_tag(port, rt)){
    case Lam:{
      PORT bindr = get_s(port, rt)[0];
      PORT var = get_port(bindr, rt);
      if (get_loc(var) != get_loc(port) || get_side(var) != 1){
        error("Lambda variable does not point to the lambda");
      }
      _check(port | 1, seen, rt);
    }
    case Dup:{
      PORT other = get_s(port, rt)[1] ^ owner;
      if (get_loc(other) != get_loc(owner)) error("other does not point to dup");
      if (get_side(other) == get_side(owner)) error("other and owner have the same side");
      _check(port | 0, seen, rt);
    }
    case Sup: case App:{
      _check(port | 0, seen, rt);
      _check(port | 1, seen, rt);
    }
    default: break;
  }

}

void check_term(PORT term, Runtime* rt){
  _check(term, NULL, rt);
}

void erase(PORT owner, Runtime* rt){
  PORT port = get_port(owner, rt);
  tree(rt);
  printf("ERASE: %s\n", port_fmt(port, rt));

  switch (get_tag(port, rt)){

    case Lam:
      if (get_side(port) == 1){
        printf("ERASE LAM VAR %s\n", port_fmt(port ^ 1, rt));
        // set_port(port ^ 1 , new_node(ERA, 0, rt), rt);
        return;
      }
      erase(get_s(port, rt)[1], rt);
      PORT var = get_s(port, rt)[0];
      // erase(var, rt);
      break;
    case Sup:
      erase(get_s(port, rt)[0], rt);
      erase(get_s(port, rt)[1], rt);
      break;
    default: break;
  }



  
}


void var_replace(PORT owner, PORT var, Runtime* rt){
  PORT data = get_port(owner, rt);
  if (get_tag(data, rt) == Lam && get_side(data) == 1){
    set_port( to_s0(data), var, rt);
  }
  set_port(var, data, rt);
}


void dup_replace(PORT owner, PORT a_owner, PORT b_owner, Runtime* rt){
  PORT dup = get_port(owner, rt);

  PORT other;
  get_dup_aux(&owner, &other, rt);
  var_replace(a_owner, owner, rt);
  var_replace(b_owner, other, rt);
}


void app_lam(PORT owner, PORT app, PORT lam, Runtime* rt){
  PORT var = get_s(lam, rt)[0];
  var_replace(app | 1, var, rt);
  var_replace(lam | 1, owner, rt);
  check_term(owner, rt);
}

PORT mk_dup(PORT a, PORT b, PORT t, int label, Runtime* rt){
  PORT dup = new_node(Dup, label, rt);
  set_dup_aux(dup, a, b, rt);
  set_port(a, new_port(get_loc(dup), 0), rt);
  set_port(b, new_port(get_loc(dup), 1), rt);
  set_port(dup, t, rt);  
  return new_port(get_loc(dup), 0);
}

void app_sup(PORT owner, PORT app, PORT sup, Runtime* rt){

  PORT FA = get_s(sup, rt)[0];
  PORT FB = get_s(sup, rt)[1];

  PORT arg = get_s(app, rt)[1];
  PORT app1 = new_node(App, 0, rt);
  PORT app2 = new_node(App, 0, rt);

  set_port(app1, FA, rt);
  set_port(app2, FB, rt);

  mk_dup(new_port(get_loc(app1), 1),new_port(get_loc(app2), 1),arg,get_label(sup, rt),rt);
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

  PORT s1 = get_s(sup, rt)[0];
  PORT s2 = get_s(sup, rt)[1];

  if (dlab == slab){
    dup_replace(owner, sup | 0, sup | 1, rt);
  }else{

    PORT S1 = new_node(Sup, slab, rt);
    PORT S2 = new_node(Sup, slab, rt);

    mk_dup(S1 | 0, S2 | 0, s1, dlab, rt);
    mk_dup(S1 | 1, S2 | 1, s2, dlab, rt);

    PORT other;
    get_dup_aux(&owner, &other, rt);
    set_port(owner, S1, rt);
    set_port(other, S2, rt);
  }
}


void set_var(PORT target, PORT lam, Runtime* rt){
  set_port(target, lam | 1, rt);
  set_port(lam | 0, target, rt);
}


void dup_lam(PORT owner, PORT dup, PORT lam, Runtime* rt){


  int lab = get_label(dup, rt);

  PORT var = get_s(lam, rt)[0];
  PORT L1 = new_node(Lam, 0, rt);
  PORT L2 = new_node(Lam, 0, rt);


  PORT varsup = new_node(Sup, lab, rt);
  set_var(varsup | 0, L1, rt);
  set_var(varsup | 1, L2, rt);
  set_port(var, varsup, rt);


  PORT bod = get_s(lam, rt)[1];
  mk_dup(L1 | 1, L2 | 1, bod, lab, rt);


  PORT other;
  get_dup_aux(&owner, &other, rt);

  set_port(owner, L1, rt);
  set_port(other, L2, rt);
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
    if (DEBUG)
      printf("REDEX: %s <> %s\n", tag_fmt(tag), tag_fmt(otag));
    handler(owner, term, other, rt);
    rt->steps ++;
    return 1;
  }
  return 0;
}

int strong_form = 0;
BST* strong_form_seen = NULL;


// #defMAX_STEPS = 1000;

int reduce(PORT owner, BST* ctx, Runtime* rt){

  PORT term = get_port(owner, rt);
  if (get_tag(term, rt) == Lam && get_side(term) == 1) return 0;

  int succ = 0;
  while (handle_redex(owner, term, rt)  ){
    succ = 1;
    term = get_port(owner, rt);
    if (DEBUG) tree(rt);
    
  }


  Tag tag = get_tag(term, rt);

  char * stag = port_fmt(term, rt);

  switch (tag){
    case App:{
      LOC loc = get_loc(term);
      if (reduce(new_port(loc, 0), ctx, rt)) succ |= reduce(owner, ctx, rt);
      if (ctx != NULL){
        reduce(new_port(loc, 1), ctx, rt);
      }
      break;
    }
    case Dup:{ 
      LOC duploc = get_loc(term);
      if (ctx != NULL){  
        if (contains(ctx, duploc)) return 0;
        insert(ctx, duploc);
      }
      if (reduce(new_port(duploc, 0), ctx, rt)) reduce(owner, ctx, rt);
      break;
    }
    case Lam:
      reduce(new_port(get_loc(term), 1), ctx, rt);
      break;
    case Sup:
      reduce(new_port(get_loc(term), 0), ctx, rt);
      reduce(new_port(get_loc(term), 1), ctx, rt); 
      break;
    default: break;
  }
  return succ;
}



int run(Runtime* rt, int steps){

  rt->fuel = steps;
  rt->steps = 0;

  PORT root = rt->root;
  BST* ctx = insert(NULL, get_loc(root));
  if (DEBUG) tree(rt);
  reduce(root, ctx, rt);
  return rt->steps;  
    
}


