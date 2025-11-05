#include <stdatomic.h>
#include <string.h>
#include <stdlib.h>
#include <stdio.h>


#define RED     "\x1b[31m"
#define GREEN   "\x1b[32m"
#define YELLOW  "\x1b[33m"
#define BLUE    "\x1b[34m"
#define RESET   "\x1b[0m"


int DEBUG = 1;
void set_debug(int debug){ DEBUG = debug; }

void debug(char* content){if (DEBUG) printf(YELLOW "DEBUG: %s" RESET, content);}

void error(char* content){
  fprintf(stderr, RED "Error: %s\n" RESET, content);
  exit(1);
}

typedef enum Tag{ Tag_App, Tag_Lam, Tag_Sup, Tag_Dup, Tag_Dup2, Tag_Null, Tag_Prim, Tag_Freed }Tag;

typedef struct IC{ Tag tag; int label; struct IC* s0; struct IC* s1; }IC;

#define MAX_ICS 1<<20

typedef struct Runtime{
  IC* root;
  IC ICs[MAX_ICS];
  int empty_index;
  int IC_ctr;
  IC* free_list;
  int steps;
} Runtime;

char* tag_names[9] = { "App", "Lam", "Sup", "Dup", "Dup2", "Null", "Var", "Prim", "Freed" };

char * IC_format(IC* IC){
  if (DEBUG >= 1){
    char*buf = malloc(sizeof(char) * 20);
    sprintf(buf, "%s %p", tag_names[IC->tag], IC);
    return buf;
  }
  return tag_names[IC->tag];
}

IC* empty_IC(int tag, int label, Runtime* runtime){

  IC* IC = NULL;
  if (runtime->free_list != NULL){
    IC = runtime->free_list;
    runtime->free_list = IC->s0;
  }else{
    IC = &runtime->ICs[runtime-> empty_index ++ ];
    if (runtime->empty_index >= MAX_ICS) error("Error: MAX_ICS reached\n");
  }
  runtime->IC_ctr ++;
  IC->tag = tag;
  IC->label = label;
  IC->s0 = NULL;
  IC->s1 = NULL;

  return IC;
}

void free_IC(IC* IC, Runtime* runtime){
  if (IC->tag == Tag_Freed){
    printf(RED "Error: IC %p is already freed\n", IC);
    exit(1);
  }
  IC->tag = Tag_Freed;
  runtime->IC_ctr --;
  IC->s0 = runtime->free_list;
  runtime->free_list = IC;
}

void set_port(IC* ic, int side, IC* port){
  if (DEBUG >= 2) printf("set_port: %p %d %p\n", ic, side, port);
  if (side == 0) ic->s0 = port;
  else ic->s1 = port;
}

void set_auxs(IC* ic, IC* s0, IC* s1){
  ic->s0 = s0;
  ic->s1 = s1;
}

IC* get_root(Runtime* runtime){return runtime->root;}
IC* set_root(IC* root, Runtime* runtime){runtime->root = root; return root;}
int get_tag(IC* IC){return IC->tag;}
int get_label(IC* IC){return IC->label;}


IC* port_info(IC* ic, int s, int loc){
  return loc ? (s ? (IC*) &(ic->s1) : (IC*) &(ic->s0)) : (s ? ic->s1 : ic->s0);
}


IC* new_IC(Tag tag, int label, IC* s0, IC* s1, Runtime* runtime){
  IC* IC = empty_IC(tag, label, runtime);
  IC->s0 = s0;
  IC->s1 = s1;
  if (DEBUG >= 2) printf("new IC: %s\n", IC_format(IC));
  return IC;
}


Runtime* new_runtime(){
  Runtime* runtime = calloc(1, sizeof(Runtime));
  runtime->free_list = NULL;
  return runtime;
}


typedef void* P;


IC* ID(Runtime* runtime){
  IC* id = empty_IC(Tag_Lam, 0, runtime);
  IC** loc = &id->s0;
  id->s1 = (IC*) loc;
  return id;
};

IC* c1(Runtime* runtime){
  IC* l1 = empty_IC(Tag_Lam, 0, runtime);
  IC* l2 = empty_IC(Tag_Lam, 0, runtime);
  l1->s0 = l2;
  l1->s1 = (IC*) &(l2->s0);
  return l1;
}



IC* mk_app(IC* f, IC* x, Runtime* runtime){
  IC* app = calloc(1, sizeof(IC));
  app->tag = Tag_App;
  app->s0 = f;
  app->s1 = x;
  return app;
}

void APP_LAM(IC** app, IC* lam, Runtime* runtime){
  printf("APP_LAM\n");
  IC** loc = (IC**) (*app)->s1;



  (*app) = lam->s0;
}

void APP_SUP(IC** app, IC* sup, Runtime* runtime){
  error("TODO");
}

void APP_NULL(IC** app, IC* null, Runtime* runtime){
  error("TODO");
}
void DUP_LAM(IC** dup, IC* lam, Runtime* runtime){
  error("TODO");
}
void DUP_SUP(IC** dup, IC* sup, Runtime* runtime){
  error("TODO");
}
void DUP_NULL(IC** dup, IC* null, Runtime* runtime){
  error("TODO");
}

int handle_redex(IC** term, IC* other, Runtime* runtime){

  void (*handler)(IC**, IC*, Runtime*) = NULL;
  if ((*term)->tag == Tag_App){
    handler = other->tag == Tag_Lam ? APP_LAM : other->tag == Tag_Sup ? APP_SUP : other->tag == Tag_Null ? APP_NULL : NULL;
  }else if ((*term)->tag == Tag_Dup || (*term)->tag == Tag_Dup2){
    handler = other->tag == Tag_Lam ? DUP_LAM : other->tag == Tag_Sup ? DUP_SUP : other->tag == Tag_Null ? DUP_NULL : NULL;
  }
  if (handler != NULL){
    handler(term, other, runtime);
    return 1;
  }
  return 0;
}

void applam(IC** app, IC* lam, Runtime* runtime){

  IC** loc = (IC**) (lam)->s1;
  *loc = (*app)->s1;
  (*app) = lam->s0;
}


int run(int Nsteps, Runtime* runtime){

  IC* term = runtime->root;

  applam(&runtime->root, runtime->root->s0, runtime);

  return 1; 

}

