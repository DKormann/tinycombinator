Taelin — 02/11/2025, 01:40
we did! that's what the interaction calculus is about
you can apply essentially the same compilation scheme as Rust
BlobKat

 — 02/11/2025, 01:42
eli5
Taelin — 02/11/2025, 01:43
so, how would you compile the affine λ-calculus to assembly?
think about it for a moment in case you haven't already
you can basically translate it 1-to-1 to C, right?
so, the affine λ-calculus basically gives you the fastest subset of Haskell / Scheme / etc.
etiamz — 02/11/2025, 01:45
By compilation, I mean compiling an input interaction net to direct code that doesn't have the interpreter overhead, be it interaction calculus or some other machinery.
BlobKat

 — 02/11/2025, 01:45
brief me on "affine" lambda calculus
Taelin — 02/11/2025, 01:45
there is no overhead... at all. C is also a superset of the affine λ-calculus...
well not quite since it doesn't support closures, but still
that's what I mean when I said you can translate it 1-to-1 to C with no overhead
Taelin — 02/11/2025, 01:46
the lambda calculus, except variables can only be used at most once

Taelin — 02/11/2025, 01:47
this greatly simplifies things and also makes it inherently faster. for one, name capture avoiding substitution is trivial, and beta-reduction is O(1)
BlobKat

 — 02/11/2025, 01:47
ok
Taelin — 02/11/2025, 01:48
substitution goes from O(N^2) to O(1), so, that's quite major
and it is not just O(1), it is also fairly lightweight. on HVM4, substitution requires a single atomic exchange
not even a CAS
so, literally 1 asm instruction
and again, for similar reasons, we can translate HVM4 functions to C directly, so, most programs you write on it will be as fast as C (once compiled) - no difference at all

Taelin — 02/11/2025, 01:50
uh, name a functional language whose beta reduction isn't 10x-100x slower than that
also it is just a single write on single threaded execution
BlobKat

 — 02/11/2025, 01:51
atomic exchange during compilation? ah...
Taelin — 02/11/2025, 01:51
what do you mean

Taelin — 02/11/2025, 01:51
it is okay
there is no atomic exchange during compilation
compilation is the process of turning HVM4 functions into C functions

Taelin — 02/11/2025, 01:51
beta reduction = applying a function to an argument
ex: in javascript, (function(x) { return x })(777) does 1 beta-reduction
this happens at runtime, not compile time
BlobKat

 — 02/11/2025, 01:52
why would it be way slower in other languages?
Taelin — 02/11/2025, 01:52
I mean you can beta-reduce at compile time, that's called inlining, but that's not what we're talking about
etiamz — 02/11/2025, 01:53
How do you capture the situation when a superposition faces applicator's principal port?
An applicator is usually static code, but this situation asks to duplicate it at run-time.
Taelin — 02/11/2025, 01:53
in javascript, beta-reduction is slower because it implements them by closures, which is a fairly complex structure. so, applying a function to an argument definitely takes quite a bit more than just 1 u64 write
BlobKat

 — 02/11/2025, 01:53
or, just, dont? 
what lambda would do in 5000 lambda expression JS would do in 5 functions
in JS we dont use closures for every tiny thing
Taelin — 02/11/2025, 01:55
I think you're confused, neither do we on HVM4
I'm talking about function application on HVM4 being faster than in JS (and anywhere else)
so, any time you need to apply a function in JS, HVM4 would do the same "thing" faster
that is one specific operation
BlobKat

 — 02/11/2025, 01:56
is HVM4 a superset of affine lamda calculus? 
Taelin — 02/11/2025, 01:56
machine integers, loops etc. would work identically as in C
Taelin — 02/11/2025, 01:56
yes!
BlobKat

 — 02/11/2025, 01:56
ok
Taelin — 02/11/2025, 01:57
it extends the affine λ-calculus with:
machine integers
loops
branching
algebraic datatypes (/structs, union, etc.)
so, basically C function

it also extends it with:
superpositions
duplications

which are new things, not related to C

 — 02/11/2025, 01:58
Superpositions????

etiamz — 02/11/2025, 01:47
But then you still need duplicators and superpositions if you want to capture non-affine usage as well?

Taelin — 02/11/2025, 01:58
for now, we don't do any inlining, but we'll soon have very direct C integration (like Zig) so the inlining happens on C functions
BlobKat

 — 02/11/2025, 01:58
how about LLVM?


Taelin — 02/11/2025, 01:59
this is a great question and is something I've worked on during the last few months. it is not complex, but is surprisignly hard to get right. HVM4 has a solution and a lot of insights on that
Taelin — 02/11/2025, 01:59

Taelin — 02/11/2025, 02:00
also there are no interaction net nodes or "ports" on HVM4, it is just the interaction calculus

 — 02/11/2025, 04:03
bro if you want i can explain this to u in vc, clearly you are confused
!zen [mrsteed is 🐐 ]

 — 02/11/2025, 04:05
it means he’s not actualy using a graph datastructure under the hood
!zen [mrsteed is 🐐 ]

 — 02/11/2025, 04:17
I was curious, could you explain your solution to affine lambda calculus not being turing complete on its own?
and if you use duplication, isn’t that an expensive operation?
Franchu — 02/11/2025, 05:41
This is very cool haha
Franchu — 02/11/2025, 05:45
how do you compile closures to C? Is it lambda lifting?
Hidden — 02/11/2025, 08:09


 — 02/11/2025, 16:54
ok sure later
Taelin — 02/11/2025, 18:33
yes
but this isn't true either
you only get with substitution chains if you do N beta reductions
so the cost per beta reduction is still O(1)
