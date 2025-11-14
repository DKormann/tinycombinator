

each node in IC has 3 Ports but only 2 ports per node are encoded

there are psitive and negative ports
all positive ports are encoded!

APP:
  + MAIN (+)
  - AUX1 (+)

LAM:
  - AUX1 (-)
  - AUX2 (+)

SUP:
  - AUX1 (+)
  - AUX2 (+)

DUP:
  - MAIN (+)
  - AUX1 xor AUX2 (-)

ROOT:
  - MAIN (+)

ERA:
  - MAIN (+)


negative ports point towards a supstiution location
positive ports point towards a term value

each port in the C encoding has a location wich stands for the node it points to and a boolean flag which indicates which port it points to.
The exact flag meaning depends on the polarity of the pointing port

positive ports point towards a term value this can be a port that is not encoded. for example a term could be aux2 port of App, think: the result of the application.
whereas negative ports only can point to encoded ports. (all positive ports are encoded!)

The flag on a negative port always encodes if its the first or second encoded port its pointing towards.
The positive port could point to encoded or unencoded ports.

Side specifies whether a port is encoded first or second in C. Since we encode only 2 ports there are only 2 sides.

for negative ports the flag equals the side.
for positive ports its more complicated.


positive ports: (pointing towards a term value)
  flag = 0:
    target = App: AUX2 (side none)
    target = Lam: MAIN (side none)
    target = DUP: AUX1 (side 1)
    target = SUP: MAIN (side none)
  flag = 1:
    target = Lam: AUX1 (side 0)
    target = DUP: AUX2 (side 1)

side 1 of dup contains both AUX ports xored together.



# substitution

a Lam aux1 represents a variable it always points to a value.
the value port it points to always needs to point back at the Lam AUX1 port.

when reducing the lambda you write into the location the lambda points to a new pointer.
when moving the location you need to update LAM AUX1 to point to the new location.
