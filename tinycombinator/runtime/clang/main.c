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

Term* get_term(PORT port, Runtime* runtime){
  return &runtime->stack[get_loc(port)];
}



PORT* get_s(PORT port, Runtime* runtime){
  return get_term(port, runtime)->s;
}

Tag get_tag(PORT port, Runtime* runtime){
  return get_term(port, runtime)->tag;
}

int get_label(PORT port, Runtime* runtime){
  return get_term(port, runtime)->label;
}

void set_tag(PORT port, Tag tag, Runtime* runtime){
  get_term(port, runtime)->tag = tag;
}

void set_label(PORT port, int label, Runtime* runtime){
  get_term(port, runtime)->label = label;
}






Runtime* new_runtime(){
  Runtime* runtime = calloc(1, sizeof(Runtime));
  return runtime;
}


void set_root(LOC root, Runtime* runtime){
  runtime->root = root;
}

LOC get_root(Runtime* runtime){
  return runtime->root;
}

void error(char* content){
  fprintf(stderr, RED "Error: %s\n" RESET, content);
  exit(1);
}

void set_port(PORT port, PORT content, Runtime* runtime){
  get_s(port, runtime)[get_side(port)] = content;
}

PORT get_port(PORT port, Runtime* runtime){
  // return get_s(port, runtime)[get_side(port)];
  return runtime->stack[get_loc(port)].s[get_side(port)];
}

void set_dup_aux(PORT port, PORT a, PORT b, Runtime* runtime){
  if (DEBUG && get_tag(port, runtime) != Dup) error("cannot set aux ports of non-dup");
  get_s(port, runtime)[1] = a ^ b;
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


char* port_fmt(PORT port){
  char*buf = malloc(sizeof(char) * 20);
  sprintf(buf, "<%d %d>", get_loc(port), get_side(port));
  return buf;
}


char* term_fmt(PORT port, Runtime* runtime){
  // Term* term = _port_node(port, runtime);
  Term* term = get_term(port, runtime);
  if (DEBUG >= 1){
    char*buf = malloc(sizeof(char) * 20);
    char* a = port_fmt(term->s[0]);
    char* b = port_fmt(term->s[1]);
    sprintf(buf, "%s: %s %s", tag_fmt(term), a,b);
    free(a);
    free(b);
    return buf;
  }
  return tag_fmt(term);
}



PORT new_node(Tag tag, int label, Runtime* runtime){

  PORT port = 0;
  if (runtime->free_list != 0){
    port = runtime->free_list;
    runtime->free_list = get_port(port, runtime);
  }else{
    port = runtime->empty;
    runtime->empty = new_port(get_loc(runtime->empty) + 1, 0);
    if (get_loc(runtime->empty) >= MAX_TERMS) error("Error: MAX_TERMS reached\n");
  }
  runtime->node_ctr ++;
  set_tag(port, tag, runtime);
  set_label(port, label, runtime);
  get_s(port, runtime)[0] = 0;
  get_s(port, runtime)[1] = 0;

  return port;
}

void free_node(PORT port, Runtime* runtime){
  if (get_tag(port, runtime) == Freed){
    printf(RED "Error: Term %s is already freed\n", term_fmt(port, runtime));
    exit(1);
  }
  set_tag(port, Freed, runtime);
  set_port(port, runtime->free_list, runtime);
  runtime->free_list = port;
}

int is_var(PORT port, Runtime* runtime){
  return (get_label(port, runtime) == Lam && get_side(port)) || get_label(port, runtime) == Dup;
}

void subs(PORT src, PORT dst, Runtime* runtime){
  PORT src_target = get_port(src, runtime);

  if (is_var(src_target, runtime)){
    error("TODO var backlink update");
  }

  set_port(dst, src, runtime);
}


void erase(PORT port, Runtime* runtime){
  printf("ERASE %s\n", port_fmt(port));
  LOC loc = get_loc(port);
  int side = get_side(port);
  if (get_tag(port, runtime) == Lam && get_side(port) == 1){
    printf("UPDATE VAR BACKELINK\n");
    set_port(port, new_node(ERA, 0 , runtime), runtime);
  }
}


void app_lam(PORT* app, PORT lam, Runtime* runtime){
  printf("APP_LAM\n");
  DEBUG=1;  
  if (DEBUG) printf("APP: %d %s\n", *app, term_fmt(*app, runtime));

  PORT arg = get_s(*app, runtime)[1];
  PORT var = get_s(lam, runtime)[0];

  printf("ARG: %d %s\n", arg, term_fmt(arg, runtime));
  printf("VAR: %d %s\n", var, term_fmt(var, runtime));

  subs(arg, var, runtime);
  PORT bod = get_s(lam, runtime)[1];
  printf("bod: %d %s\n", bod, term_fmt(bod, runtime));

  // set_port(*app, bod, runtime);
  // set_port( *app, lam, runtime);
  *app = bod;

}

void app_sup(PORT* buf, PORT app, Runtime* runtime){
  printf("APP_SUP\n");
}

void app_null(PORT* buf, PORT app, Runtime* runtime){
  printf("APP_NULL\n");
}

void dup_lam(PORT* buf, PORT lam, Runtime* runtime){
  printf("DUP_LAM\n");
}

void dup_sup(PORT* buf, PORT sup, Runtime* runtime){
  printf("DUP_SUP\n");
}

void dup_null(PORT* buf, PORT null, Runtime* runtime){
  printf("DUP_NULL\n");
}




int handle_redex(PORT* term, Runtime* runtime){

  if (runtime->steps >= runtime->fuel) return 0;
  void (*handler)(PORT* , PORT, Runtime*) = NULL;

  Tag tag = get_tag(*term, runtime);
  PORT other = get_s(*term, runtime)[0];
  Tag otag = get_tag(other, runtime);

  switch (tag){
    case App:
      switch (otag){
        case Lam: handler = app_lam; break;
        case Sup: handler = app_sup; break;
        case Null: handler = app_null; break;
        default: break;
      }
      break;
    case Dup:
      switch (otag){
        case Lam: handler = dup_lam; break;
        case Sup: handler = dup_sup; break;
        case Null: handler = dup_null; break;
        default: break;
      }
      break;
    default: break;
  }
  if (handler != NULL){
    handler(term, other, runtime);
    runtime->fuel ++;
    return 1;
  }
  return 0;
}

int strong_form = 0;
BST* strong_form_seen = NULL;

void reduce(PORT* term, Runtime* runtime){



  if (handle_redex(term, runtime)){
    printf("REDUCED\n");
    return;
  }

  switch (get_tag(*term, runtime)){
    case ROOT:
      printf("ROOT\n");
      reduce(&get_s(*term, runtime)[0], runtime);
      break;
    case Lam:{

      PORT* bod = &get_s(*term, runtime)[1];
      reduce(bod, runtime);
      break;
    }
    default: break;


  }



}



int run(Runtime* runtime, int steps){



  printf("RUN\n");
  runtime->fuel = steps;
  runtime->steps = 0;

  PORT* root = &runtime->root;

  reduce(root, runtime);

  PORT* app = get_s(*root, runtime);
  PORT lam = get_s(*app, runtime)[1];


  // app_lam(app, lam, runtime);

  // set_port(PORT port, PORT content, Runtime *runtime)

  // PORT ree = get_s(*root, runtime)[0];
  // PORT bod = get_s(ree, runtime)[1];

  // printf("RES: %d %d\n", get_loc(ree), get_loc(ree));

  return runtime->steps;  
    
}


