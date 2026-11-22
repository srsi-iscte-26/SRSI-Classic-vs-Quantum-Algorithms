from src.classical.saes import encrypt

# Testa todas as chaves variando os ultimos n_bits (os restantes são fixos)
# Devolve as chaves válidas e o número de cifragens realizadas 
def brute_force_search(plaintext, ciphertext, n_bits, fixed_key_bits):
    if not 1 <= n_bits <= 16:
        raise ValueError("n_bits must be between 1 and 16.")

    if not 0 <= plaintext <= 0xFFFF:
        raise ValueError("Plaintext must be a 16-bit value.")

    if not 0 <= ciphertext <= 0xFFFF:
        raise ValueError("Ciphertext must be a 16-bit value.")

    if not 0 <= fixed_key_bits <= 0xFFFF:
        raise ValueError("fixed_key_bits must be a 16-bit value.")

    variable_mask = (1 << n_bits) - 1

    if fixed_key_bits & variable_mask:
        raise ValueError("The variable bits in fixed_key_bits must be zero.")

    matches = []
    attempts = 0

    for variable_bits in range(1 << n_bits):
        candidate_key = fixed_key_bits | variable_bits
        candidate_ciphertext = encrypt(plaintext, candidate_key)
        attempts += 1
        if candidate_ciphertext == ciphertext:
            matches.append(candidate_key)

    return matches, attempts