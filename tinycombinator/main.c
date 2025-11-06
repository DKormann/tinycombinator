#include <stdatomic.h>
#include <stdint.h>
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



typedef int32_t LOC;



typedef struct IC{
  Tag tag;
  int label;
  int32_t s[2]; // last bit signifies target side or if target is var of lam
} IC;


// for LAM s[1] is the var. its side points to the target port number.
// for all other ports the side says whether its the var of a lam

#define MAX_ICS 1<<20

typedef struct Runtime{
  LOC root;
  IC ICs[MAX_ICS];
  int empty_index;
  int IC_ctr;
  LOC free_list;
  int steps;
} Runtime;



IC* get_ic(LOC l, Runtime* runtime){
  return &runtime->ICs[l];
}

int get_tag(LOC l, Runtime* runtime){
  return runtime->ICs[l].tag;
}

void set_port(LOC ic, int s, LOC target, int side, Runtime* runtime){
  get_ic(ic, runtime)->s[s] = target << 1 | side;
}


int port_side( LOC l , int side, Runtime* runtime){
  return runtime->ICs[l].s[side] & 1;
}

int port_target( LOC l, int side, Runtime* runtime){
  return runtime->ICs[l].s[side] >> 1;
}

void var_lam(LOC lam, LOC target, int side, Runtime* runtime){
  set_port(lam, 1, target, side, runtime);
  set_port(target, side, lam, 1, runtime);
}


Runtime* new_runtime(){
  Runtime* runtime = calloc(1, sizeof(Runtime));
  return runtime;
}



char* tag_names[9] = { "App", "Lam", "Sup", "Dup", "Dup2", "Null", "Var", "Prim", "Freed" };

char * IC_format(IC* IC){
  if (DEBUG >= 1){
    char*buf = malloc(sizeof(char) * 20);
    sprintf(buf, "%s %p", tag_names[IC->tag], IC);
    return buf;
  }
  return tag_names[IC->tag];
}

LOC empty_IC(int tag, int label, Runtime* runtime){

  LOC res = 0;
  IC* IC = NULL;
  if (runtime->free_list != 0){
    res = runtime->free_list;
    IC = get_ic(res, runtime);
    runtime->free_list = IC->s[0];
  }else{
    res = runtime->empty_index ++;
    IC = get_ic(res, runtime);
    if (runtime->empty_index >= MAX_ICS) error("Error: MAX_ICS reached\n");
  }
  runtime->IC_ctr ++;
  IC->tag = tag;
  IC->label = label;
  IC->s[0] = 0;
  IC->s[1] = 0;

  return res;
}

void free_IC(LOC loc, Runtime* runtime){
  IC* IC = get_ic(loc, runtime);
  if (IC->tag == Tag_Freed){
    printf(RED "Error: IC %p is already freed\n", IC);
    exit(1);
  }
  IC->tag = Tag_Freed;
  runtime->IC_ctr --;
  set_port(loc, 0, runtime->free_list, 0, runtime);
  runtime->free_list = loc;
}

LOC get_root(Runtime* runtime){
  return runtime->root;
}

void set_root(LOC root, Runtime* runtime){runtime->root = root;}


LOC ID(Runtime* runtime){
  LOC id = empty_IC(Tag_Lam, 0, runtime);
  // var_lam(id, id, 0, runtime);

  set_port(id, 0, id, 1, runtime);
  return id;
}


LOC c1(Runtime* runtime){
  LOC l1 = empty_IC(Tag_Lam, 0, runtime);
  LOC l2 = empty_IC(Tag_Lam, 0, runtime);
  var_lam(l1, l2, 0, runtime);
  set_port(l1, 0, l2, 0, runtime);
  return l1;
}


LOC mk_binary(Tag tag, int label, LOC s0, LOC s1, Runtime* runtime){
  LOC res = empty_IC(tag, label, runtime);
  set_port(res, 0, s0, 0, runtime);
  set_port(res, 1, s1, 0, runtime);
  return res;
}





// void APP_LAM(IC** app, IC* lam, Runtime* runtime){
//   (* (IC**) lam->s[1]) = (*app)->s[1];
//   (*app) = lam->s[0];
// }

// void APP_SUP(IC** app, IC* sup, Runtime* runtime){
//   error("TODO APPSUP");
// }

// void APP_NULL(IC** app, IC* null, Runtime* runtime){
//   error("TODO APPNULL");
// }

// void DUP_LAM(IC** dup, IC* lam, Runtime* runtime){
//   error("TODO DUPLAM");
// }

// void DUP_SUP(IC** dup, IC* sup, Runtime* runtime){
//   error("TODO DUPSUP");
// }
// void DUP_NULL(IC** dup, IC* null, Runtime* runtime){
//   error("TODO DUPNULL");
// }

// int handle_redex(IC** term, IC* other, Runtime* runtime){

//   void (*handler)(IC**, IC*, Runtime*) = NULL;
//   if ((*term)->tag == Tag_App){
//     handler = other->tag == Tag_Lam ? APP_LAM : other->tag == Tag_Sup ? APP_SUP : other->tag == Tag_Null ? APP_NULL : NULL;
//   }else if ((*term)->tag == Tag_Dup || (*term)->tag == Tag_Dup2){
//     handler = other->tag == Tag_Lam ? DUP_LAM : other->tag == Tag_Sup ? DUP_SUP : other->tag == Tag_Null ? DUP_NULL : NULL;
//   }
//   if (handler != NULL){
//     handler(term, other, runtime);
//     return 1;
//   }
//   return 0;
// }

// void applam(IC** app, IC* lam, Runtime* runtime){

//   IC** loc = (IC**) (lam)->s[1];
//   *loc = (*app)->s[1];
//   (*app) = lam->s[0];
// }


int run(int Nsteps, Runtime* runtime){
  // runtime->root = c1(runtime);



  runtime->root = ID(runtime);

  return 1;
}