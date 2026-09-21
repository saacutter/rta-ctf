For this task, the only thing that is provided is `rsa.enc`, which looks like the following. 
```
n1 = 608274...712081

c1 = 201700...036721

e1 = 3

n2 = 608274...712081

c2 = 297771...598737

e2 = 5
```
This includes 6 different values - `n1`, `c1`, `e1`, `n2`, `c2`, and `e2`. The file name including `rsa` indicates that we are dealing with the RSA encryption algorithm, which means we know what each of these values represent. `c` is the ciphertext which we are trying to convert into plaintext, and `n` and `e` are the public key components. As there is nothing else to work on, we can assume that the goal is to convert the ciphertext (`c`) into plaintext (`m`). 

One of the first things to notice about these values is that there is a red herring - `n1` and `n2` are the same value. This is important information because it narrows down what we can do with these values. However, given that we have two different ciphertexts with the same modulus `n`, it can be assumed that we are going to perform a common modulus attack. As `e1` and `e2` are specifically coprime, this possibility becomes even more likely.

Bezout's theorem can be used to decrypt the ciphertext to retrieve the plaintext message. As we know that `e1` and `e2` are coprime, then `gcd(e1, e2) = 1`. By Bezout's theorem, this can be used to compute `m` from `c1` and `c2`.
```py
from math import gcd

n = 608274...712081
c1 = 201700...036721
e1 = 3
c2 = 297771...598737
e2 = 5

# Adapted from https://susanou.github.io/Writeups/posts/RSA-Common-Modulus/
s1 = pow(e1, -1, e2)
s2 = (gcd(e1, e2) - e1*s1)//e2
temp = pow(c2, -1, n)
m1 = pow(c1, s1, n)
m2 = pow(temp, -s2, n)
print((m1 * m2) % n)
```

This results in the following value.
```
24855301821421549348704050020767991187216845321802454677191021172040676253112653170393885875253339310670977282755774904952155588415060425919359452742325944478438227952655259251193204434207863530072927018279439921853249351898709715161192274307992740812153018735054511871845051741163118368686606673280466222408303510656747323816669183086890447541784855508872285624991646328345643056687600999743507344938368387365884405322060537716174640625844644467554477748577936654109256204276282061507101033831101311916180932819745412367574848563805319458590706781538625770904977341551165083105210860644035575096141973536633499558383
```

Using the other value gained from the previous challenge, we can now move onto the next challenge.