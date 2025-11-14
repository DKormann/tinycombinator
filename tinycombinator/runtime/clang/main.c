#include <stdatomic.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>

typedef int32_t LOC;
typedef int32_t PORT;

typedef struct BST {
  // void *data;
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
  LOC root;
  Term stack[MAX_TERMS];

  LOC free_list;
  LOC empty_index;
  LOC node_ctr;
  int steps;
  int fuel;

} Runtime;


typedef struct Port{
  LOC loc;
  int side;
} Port;


Runtime* new_runtime(){
  Runtime* runtime = calloc(1, sizeof(Runtime));
  return runtime;
}


void set_root(LOC root, Runtime* runtime){
  runtime->root = root;
}


PORT serialize_port(Port port){
  return port.loc << 1 | port.side;
}

Port deserialize_port(PORT port){
  return (Port){
    .loc = port >> 1,
    .side = port & 1
  };
}


LOC get_root(Runtime* runtime){
  return runtime->root;
}

void error(char* content){
  fprintf(stderr, RED "Error: %s\n" RESET, content);
  exit(1);
}

Term* get_node(LOC loc, Runtime* runtime){
  return &runtime->stack[loc];
}

void set_port(Port dest, Port src, Runtime* runtime){
  // if (DEBUG) printf("SET_PORT: %d %d -> %d %d\n", dest.loc, dest.side, src.loc, src.side);
  Term* term = get_node(dest.loc, runtime);
  term->s[dest.side] = src.loc << 1 | src.side;
}

Port get_port(Port port, Runtime* runtime){
  PORT data = get_node(port.loc, runtime)->s[port.side];
  return deserialize_port(data);
}



LOC get_port_target(Port port, Runtime* runtime){
  if (DEBUG && get_node(port.loc, runtime)->tag == Dup && port.side != 0) error("cannot get singular port of DUP");
  return get_node(port.loc, runtime)->s[port.side] >> 1;
}

Tag get_tag(LOC loc, Runtime* runtime){
  return get_node(loc, runtime)->tag;
}

int get_label(LOC loc, Runtime* runtime){
  return get_node(loc, runtime)->label;
}


PORT get_other_port(LOC loc, Port getter, Runtime* runtime){
  if (DEBUG && get_node(loc, runtime)->tag != Dup) error("cannot get other port of non-dup");
  PORT packed_getter = getter.loc << 1 | getter.side;
  return get_node(loc, runtime)->s[1] ^ packed_getter;
}

Port get_other_port_as_port(LOC loc, Port getter, Runtime* runtime){
  PORT packed = get_other_port(loc, getter, runtime);
  return (Port){
    .loc = packed >> 1,
    .side = packed & 1
  };
}

void set_dup_aux(LOC loc, Port a, Port b, Runtime* runtime){
  if (DEBUG && get_node(loc, runtime)->tag != Dup) error("cannot set aux ports of non-dup");
  get_node(loc, runtime)->s[1] = (a.loc << 1 | a.side) ^ (b.loc << 1 | b.side);
}



char* tag_fmt(Term* term){
  switch (term->tag){
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


char* port_fmt(Port port){
  char*buf = malloc(sizeof(char) * 20);
  sprintf(buf, "<%d %d>", port.loc, port.side);
  return buf;
}

char* term_fmt(Term* term){
  if (DEBUG >= 1){
    char*buf = malloc(sizeof(char) * 20);
    char* a = port_fmt(deserialize_port(term->s[0]));
    char* b = port_fmt(deserialize_port(term->s[1]));
    sprintf(buf, "%s: %s %s", tag_fmt(term), a,b);
    free(a);
    free(b);
    return buf;
  }
  return tag_fmt(term);
}



LOC new_node(Tag tag, int label, Runtime* runtime){
  LOC res = 0;
  Term* term = NULL;
  if (runtime->free_list != 0){
    res = runtime->free_list;
    term = get_node(res, runtime);
    runtime->free_list = get_port_target((Port){res, 0}, runtime);
  }else{
    res = runtime->empty_index ++;
    term = get_node(res, runtime);
    if (runtime->empty_index >= MAX_TERMS) error("Error: MAX_TERMS reached\n");
  }

  runtime->node_ctr ++;
  term->tag = tag;
  term->label = label;
  term->s[0] = 0;
  term->s[1] = 0;
  return res;
}


void free_node(LOC loc, Runtime* runtime){
  Term* term = get_node(loc, runtime);
  if (term->tag == Freed){
    printf(RED "Error: Term %p is already freed\n", term);
    exit(1);
  }
  term->tag = Freed;
  runtime->node_ctr --;
  set_port((Port){loc, 0}, (Port){runtime->free_list, 0}, runtime);
  runtime->free_list = loc;
}

LOC binary_term(Tag tag, int label, LOC s0, LOC s1, Runtime* runtime){
  LOC res = new_node(tag, label, runtime);
  get_node(res, runtime)->s[0] = s0; 
  get_node(res, runtime)->s[1] = s1;
  return res;
}


void move(LOC src, LOC dst, Runtime* runtime){

  Term* dt = get_node(dst, runtime);
  Term* st = get_node(src, runtime);
  dt->tag = st->tag;
  dt->label = st->label;
  dt->s[0] = st->s[0];
  dt->s[1] = st->s[1];
  free_node(src, runtime);
}



int pos_sides[][2] = {
  [App] = {0, 1},
  [Lam] = {1, -1},
  [Dup] = {0, -1},
  [Sup] = {0, 1}
};

int is_var(Port p, Runtime* runtime){
  Term* t = get_node(p.loc, runtime);
  return (t->label == Lam && p.side) || (t->label == Dup);
}

void subs(Port src, Port dst, Runtime* runtime){

  Port src_target = get_port(src, runtime);

  if (is_var(src_target, runtime)){
    error("TODO var backlink update");
  }
  
  set_port(dst, src, runtime);
}



void app_lam(PORT* buf, LOC app, LOC lam, Runtime* runtime){
  printf("APP_LAM\n");
  DEBUG=1;
  if (DEBUG) printf("APP: %d %s\n", app, term_fmt(get_node(app, runtime)));
  if (DEBUG) printf("LAM: %d %s\n", lam, term_fmt(get_node(lam, runtime)));

  subs(get_port((Port){app, 1}, runtime), get_port((Port){lam, 0}, runtime), runtime);

  (*buf) = serialize_port(get_port((Port){lam, 1}, runtime));
}

void app_sup(PORT* buf, LOC sup, LOC app, Runtime* runtime){
  printf("APP_SUP\n");
}

void app_null(PORT* buf, LOC null, LOC app, Runtime* runtime){
  printf("APP_NULL\n");
}

void dup_lam(PORT* buf, LOC dup, LOC lam, Runtime* runtime){
  printf("DUP_LAM\n");
}

void dup_sup(PORT* buf, LOC dup, LOC sup, Runtime* runtime){
  printf("DUP_SUP\n");
}

void dup_null(PORT* buf, LOC dup, LOC null, Runtime* runtime){
  printf("DUP_NULL\n");
}

int handle_redex(PORT* buf, LOC term, LOC other, Runtime* runtime){

  if (runtime->steps >= runtime->fuel) return 0;


  void (*handler)(PORT*, LOC, LOC, Runtime*) = NULL;

  printf("<>: %d %d\n", get_tag(term, runtime), get_tag(other, runtime));
  printf("Handling redex %s %s\n", term_fmt(get_node(term, runtime)), term_fmt(get_node(other, runtime)));

  switch (get_tag(term, runtime)){
    case App:
      switch (get_tag(other, runtime)){
        case Lam: handler = app_lam; break;
        case Sup: handler = app_sup; break;
        case Null: handler = app_null; break;
        default: break;
      }
      break;
    case Dup:
      switch (get_tag(other, runtime)){
        case Lam: handler = dup_lam; break;
        case Sup: handler = dup_sup; break;
        case Null: handler = dup_null; break;
        default: break;
      }
      break;
    default: break;
  }
  if (handler != NULL){
    handler(buf, term, other, runtime);
    runtime->fuel ++;
    return 1;
  }
  return 0;
}

int strong_form = 0;
BST* strong_form_seen = NULL;

void reduce(PORT* buf, Runtime* runtime){
  printf("RED \n");

  Port port = deserialize_port(*buf);
  Term* node = get_node(port.loc, runtime);
  if (node->tag == Lam && port.side){
    printf("not a standalone term");
    return;
  }


  if (handle_redex(buf, port.loc, deserialize_port(node->s[0]).loc, runtime)){
    return reduce (buf, runtime);
  }


  switch (node->tag){
    case Lam:{
      PORT* pbod = &node->s[1];

      DEBUG=1;
      reduce(pbod, runtime);

  }
  default: break;
  }  

}



int run(Runtime* runtime, int steps){


  runtime->fuel = steps;
  runtime->steps = 0;

  LOC root = runtime->root;
  PORT* resbuf = get_node(root, runtime)->s;




  reduce(resbuf, runtime);

  Port ree = deserialize_port(get_node(root, runtime)->s[0]);
  printf("RES: %d %d\n", ree.loc, ree.side);

  return runtime->steps;
    
}


