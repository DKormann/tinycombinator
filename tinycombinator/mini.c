#define NULL (void*) 0;

typedef void* P;



P self = NULL;

typedef struct Node {
  P (*app) (P arg);
  P (*dup) (P dup);
  char* (*rep) ();
  
}Node;

struct  Fun{
  Node* node;
  P (*app) (P arg);
} Method;


P f(P x){
  return x;
}


P dup(P f, P x){
  
}


P ID(P x){
  return x;
}


P F_x;

P _F(P y){
  return y;
}

P F(P x){
  P F_x = x;
  return _F;
}

P T_x;

P _T(P y){
  return T_x;
}

P T(P x){
  T_x = x;
  return _T;
}