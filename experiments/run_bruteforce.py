from src.classical.saes import encrypt
from src.classical.brute_force import brute_force_search

PLAINTEXT = 0xD728
SECRET_KEY = 0x4AF5

CIPHERTEXT = encrypt(PLAINTEXT, SECRET_KEY)

print(f"Plaintext:  {PLAINTEXT:04X}")
print(f"Ciphertext: {CIPHERTEXT:04X}")
print()

for n_bits in (4, 8, 12):

    variable_mask = (1 << n_bits) - 1
    fixed_key_bits = SECRET_KEY & (0xFFFF ^ variable_mask)

    matches, attempts = brute_force_search(plaintext=PLAINTEXT, ciphertext=CIPHERTEXT, n_bits=n_bits, fixed_key_bits=fixed_key_bits)

    print(f"Search space: {n_bits} variable bits")
    print(f"Fixed bits:   {fixed_key_bits:04X}")
    print(f"Attempts:     {attempts}")
    print(f"Valid keys:   {[f'{key:04X}' for key in matches]}")
    print(f"Original key found: {SECRET_KEY in matches}")
    print()