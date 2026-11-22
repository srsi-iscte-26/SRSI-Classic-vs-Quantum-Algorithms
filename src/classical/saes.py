# S-AES (Simplified AES)
# Tamanho do bloco: 16 bits
# Tamanho da chave: 16 bits 

# Substitution box
SBOX = [
    0x9, 0x4, 0xA, 0xB,
    0xD, 0x1, 0x8, 0x5,
    0x6, 0x2, 0x0, 0x3,
    0xC, 0xE, 0xF, 0x7
]

# Inverse substitution box
INV_SBOX = [
    0xA, 0x5, 0x9, 0xB,
    0x1, 0x7, 0x8, 0xF,
    0x6, 0x0, 0x2, 0x3,
    0xC, 0x4, 0xD, 0xE
]

# -------------------------
# Key Expansion 
# -------------------------

# Troca cada metade do byte (2 nibbles) pela SBOX (ex: 0xAB -> SBOX[A] e SBOX[B] juntos)
def sub_nibbles(value):
    return ((SBOX[(value >> 4) & 0xF] << 4) | SBOX[value & 0xF])


# Troca os dois nibbles de um byte (ex: 0xAB -> 0xBA)
def rot_nibbles(value):
    return ((value << 4) & 0xFF) | (value >> 4)

def g_function(value, round_constant):
    return sub_nibbles(rot_nibbles(value)) ^ round_constant

def key_expansion(key):
    # Separa a chave em 2 bytes: w0 (esq) e w1 (dir)
    w0 = (key >> 8) & 0xFF
    w1 = key & 0xFF

    # Gera w2, w3 a partir de w1 (com constante 0x80)
    w2 = w0 ^ g_function(w1, 0x80)
    w3 = w2 ^ w1

    # Gera w4, w5 a partir de w3 (com constante 0x30)
    w4 = w2 ^ g_function(w3, 0x30)
    w5 = w4 ^ w3

    # Junta em pares -> 3 sub-chaves de 16 bits
    k0 = (w0 << 8) | w1
    k1 = (w2 << 8) | w3
    k2 = (w4 << 8) | w5

    return k0, k1, k2


# -------------------------
# Representação do estado 
# -------------------------

# Converte um valor de 16 bits numa matriz de estado 2x2
def to_state(value):
    return [
        [(value >> 12) & 0xF, (value >> 4) & 0xF],
        [(value >> 8) & 0xF, value & 0xF]
    ]

# Converte a matriz de estado de volta para 16 bits
def from_state(state):
    return (
        (state[0][0] << 12)
        | (state[1][0] << 8)
        | (state[0][1] << 4)
        | state[1][1]
    )

# Mistura a chave com o estado (XOR)
def add_round_key(state, key):
    return to_state(from_state(state) ^ key)

# -------------------------
# SubNib e ShiftRow 
# -------------------------

# Troca cada nibble da matriz pela SBOX (não-linearidade)
def sub_nib_state(state):
    return [
        [SBOX[value] for value in row]
        for row in state
    ]


# Troca cada nibble pela INV_SBOX (usado ao decifrar)
def inv_sub_nib_state(state):
    return [
        [INV_SBOX[value] for value in row]
        for row in state
    ]

# Troca os nibbles da linha 1
def shift_rows(state):
    return [
        state[0][:],
        [state[1][1], state[1][0]]
    ]

# -------------------------
# Finite field multiplication: GF(2^4)
# -------------------------

# Multiplica dois nibbles (0-F) numa Galois Field
def gf_multiply(a, b):
    result = 0

    for _ in range(4):
        if b & 1:
            result ^= a

        b >>= 1
        a <<= 1

        # Polinómio irredutivel: x^4 + x + 1
        if a & 0x10:
            a ^= 0x13

    return result & 0xF

# -------------------------
# MixColumns
# -------------------------

# Mistura os nibbles de cada coluna
def mix_columns(state):
    return [
        [
            state[0][0] ^ gf_multiply(4, state[1][0]),
            state[0][1] ^ gf_multiply(4, state[1][1])
        ],
        [
            gf_multiply(4, state[0][0]) ^ state[1][0],
            gf_multiply(4, state[0][1]) ^ state[1][1]
        ]
    ]


def inv_mix_columns(state):
    return [
        [
            gf_multiply(9, state[0][0]) ^ gf_multiply(2, state[1][0]),
            gf_multiply(9, state[0][1]) ^ gf_multiply(2, state[1][1])
        ],
        [
            gf_multiply(2, state[0][0]) ^ gf_multiply(9, state[1][0]),
            gf_multiply(2, state[0][1]) ^ gf_multiply(9, state[1][1])
        ]
    ]


# -------------------------
# Encriptação
# -------------------------

def encrypt(plaintext, key):
    k0, k1, k2 = key_expansion(key)
    state = to_state(plaintext)
    state = add_round_key(state, k0)

    # Round 1
    state = sub_nib_state(state)
    state = shift_rows(state)
    state = mix_columns(state)
    state = add_round_key(state, k1)

    # Round 2
    state = sub_nib_state(state)
    state = shift_rows(state)
    state = add_round_key(state, k2)

    return from_state(state)

# -------------------------
# Desencriptação
# -------------------------

def decrypt(ciphertext, key):

    k0, k1, k2 = key_expansion(key)

    state = to_state(ciphertext)

    state = add_round_key(state, k2)

    # Inverse Round 2
    state = shift_rows(state)
    state = inv_sub_nib_state(state)
    state = add_round_key(state, k1)

    # Inverse Round 1
    state = inv_mix_columns(state)
    state = shift_rows(state)
    state = inv_sub_nib_state(state)
    state = add_round_key(state, k0)

    return from_state(state)

