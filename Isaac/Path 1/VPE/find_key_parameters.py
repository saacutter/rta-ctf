from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization

with open("ssh", "rb") as file:
    private_key = serialization.load_ssh_private_key(
        file.read(),
        password=None
    )

numbers = private_key.private_numbers()
print("n =", numbers.p * numbers.q)

print("p =", numbers.p, "q =", numbers.q)