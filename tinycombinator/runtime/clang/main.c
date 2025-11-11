#include <stdatomic.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>

#define MAX_TERMS 1<<20

#define RED     "\x1b[31m"
#define RESET   "\x1b[0m"

int DEBUG = 0;

void set_debug(int debug){ DEBUG = debug; }

typedef enum{
  App, Lam, Dup, Sup, Null, Prim, ERA, ROOT, Freed
} Tag;

typedef int32_t LOC;

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

} Runtime;

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

Term* get_term(LOC loc, Runtime* runtime){
  return &runtime->stack[loc];
}

void set_port(LOC loc, int side, LOC target, int target_side, Runtime* runtime){
  Term* term = get_term(loc, runtime);
  term->s[side] = target << 1 | target_side;
}

int get_port_side(LOC loc, int side, Runtime* runtime){
  if (DEBUG && get_term(loc, runtime)->tag == Dup && side != 0) error("cannot get singular port of DUP");
  return get_term(loc, runtime)->s[side] & 1;
}

int get_port_target(LOC loc, int side, Runtime* runtime){
  if (DEBUG && get_term(loc, runtime)->tag == Dup && side != 0) error("cannot get singular port of DUP");
  return get_term(loc, runtime)->s[side] >> 1;
}

Tag get_tag(LOC loc, Runtime* runtime){
  return get_term(loc, runtime)->tag;
}

int get_label(LOC loc, Runtime* runtime){
  return get_term(loc, runtime)->label;
}


int get_other_port(LOC loc, LOC getter, Runtime* runtime){
  if (DEBUG && get_term(loc, runtime)->tag != Dup) error("cannot get other port of non-dup");
  return get_term(loc, runtime)->s[1] ^ getter;
}

int get_other_port_side(LOC loc, LOC getter, int getter_side, Runtime* runtime){
  getter = getter << 1 | getter_side;
  return get_other_port(loc, getter, runtime) & 1;
}

int get_other_port_target(LOC loc, LOC getter, int getter_side, Runtime* runtime){
  getter = getter << 1 | getter_side;
  return get_other_port(loc, getter, runtime) >> 1;
}

void set_dup_aux(LOC loc, LOC a, int a_side, LOC b, int b_side, Runtime* runtime){
  if (DEBUG && get_term(loc, runtime)->tag != Dup) error("cannot set aux ports of non-dup");
  get_term(loc, runtime)->s[1] = (a << 1 | a_side) ^ (b << 1 | b_side);
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

char* term_fmt(Term* term){
  if (DEBUG >= 1){
    char*buf = malloc(sizeof(char) * 20);
    sprintf(buf, "%s %p", tag_fmt(term), term);
    return buf;
  }
  return tag_fmt(term);
}

LOC new_term(Tag tag, int label, Runtime* runtime){
  LOC res = 0;
  Term* term = NULL;
  if (runtime->free_list != 0){
    res = runtime->free_list;
    term = get_term(res, runtime);
    runtime->free_list = get_port_target(res, 0, runtime);
  }else{
    res = runtime->empty_index ++;
    term = get_term(res, runtime);
    if (runtime->empty_index >= MAX_TERMS) error("Error: MAX_TERMS reached\n");
  }

  runtime->node_ctr ++;
  term->tag = tag;
  term->label = label;
  term->s[0] = 0;
  term->s[1] = 0;
  return res;
}


void free_term(LOC loc, Runtime* runtime){
  Term* term = get_term(loc, runtime);
  if (term->tag == Freed){
    printf(RED "Error: Term %p is already freed\n", term);
    exit(1);
  }
  term->tag = Freed;
  runtime->node_ctr --;
  set_port(loc, 0, runtime->free_list, 0, runtime);
  runtime->free_list = loc;

}

LOC binary_term(Tag tag, int label, LOC s0, LOC s1, Runtime* runtime){
  LOC res = new_term(tag, label, runtime);
  get_term(res, runtime)->s[0] = s0;
  get_term(res, runtime)->s[1] = s1;
  return res;
}
