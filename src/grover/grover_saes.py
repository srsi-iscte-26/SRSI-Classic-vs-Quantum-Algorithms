from functools import lru_cache
import numpy as np
from qiskit import QuantumCircuit
from qiskit.circuit.library import UnitaryGate
from src.classical.saes import SBOX, gf_multiply


# Constrói a porta quântica correspondente à S-box do S-AES
@lru_cache(maxsize=1)
def build_sbox_gate():
    matrix = np.zeros((16, 16), dtype=complex)
    for input_value, output_value in enumerate(SBOX):
        matrix[output_value, input_value] = 1.0

    return UnitaryGate(matrix, label="SBOX")


# Aplica a S-box aos quatro nibbles do estado
def apply_sub_nibbles(circuit, state_qubits, inverse=False):
    gate = build_sbox_gate()
    if inverse:
        gate = gate.inverse()

    for start in range(0, 16, 4):
        circuit.append(gate, state_qubits[start:start + 4])


# Troca os nibbles da segunda linha do estado
def apply_shift_rows(circuit, state_qubits):
    for bit in range(4):
        circuit.swap(state_qubits[bit], state_qubits[bit + 8])


# Aplica XOR entre o estado e uma subchave
def apply_add_round_key(circuit, state_qubits, key_qubits):
    for state_bit, key_bit in zip(state_qubits, key_qubits):
        circuit.cx(key_bit, state_bit)

# Calcula a função G reversivelmente e efetua o XOR no byte superior
def xor_g_into_word0(circuit, word0, word1, round_constant):
    sbox_gate = build_sbox_gate()
    # Trocar os nibbles do byte inferior
    for bit in range(4):
        circuit.swap(word1[bit], word1[bit + 4])

    # Aplicar SubNib aos dois nibbles
    circuit.append(sbox_gate, word1[0:4])
    circuit.append(sbox_gate, word1[4:8])

    # Aplicar a constante da ronda
    for bit in range(8):
        if (round_constant >> bit) & 1:
            circuit.x(word0[bit])

    # Efetuar o XOR da função G no byte superior
    for bit in range(8):
        circuit.cx(word1[bit], word0[bit])

    # Restaurar o byte inferior
    inverse_sbox = sbox_gate.inverse()

    circuit.append(inverse_sbox, word1[0:4])
    circuit.append(inverse_sbox, word1[4:8])

    for bit in range(4):
        circuit.swap(word1[bit], word1[bit + 4])


# Executa uma transformação da expansão de chaves ou a sua inversa
def apply_key_schedule_round(circuit, schedule_qubits, round_constant, inverse=False):
    word0 = schedule_qubits[8:16]
    word1 = schedule_qubits[0:8]
    if inverse:
        # Recuperar o byte inferior original
        for bit in range(8):
            circuit.cx(word0[bit], word1[bit])

        # Recuperar o byte superior original
        xor_g_into_word0(circuit, word0, word1, round_constant)
    else:
        # Gerar o novo byte superior
        xor_g_into_word0(circuit, word0, word1, round_constant)
        # Gerar o novo byte inferior
        for bit in range(8):
            circuit.cx(word0[bit], word1[bit])


# Constrói uma sequência de portas CNOT e SWAP equivalente ao MixColumns
@lru_cache(maxsize=1)
def get_mix_columns_operations():
    matrix = [[0 for _ in range(8)] for _ in range(8)]
    # Construir a matriz da transformação a partir da implementação clássica
    for input_bit in range(8):
        value = 1 << input_bit
        word0 = (value >> 4) & 0xF
        word1 = value & 0xF

        output0 = word0 ^ gf_multiply(4, word1)
        output1 = gf_multiply(4, word0) ^ word1

        output_value = (output0 << 4) | output1

        for output_bit in range(8):
            matrix[output_bit][input_bit] = (output_value >> output_bit) & 1

    operations = []

    # Reduzir a matriz à identidade através de operações elementares
    for column in range(8):
        pivot = next((row for row in range(column, 8) if matrix[row][column]), None)
        if pivot is None:
            raise ValueError("A transformação MixColumns não é invertível.")

        if pivot != column:
            matrix[column], matrix[pivot] = (matrix[pivot], matrix[column])

            operations.append(("swap", column, pivot))

        for row in range(8):
            if row != column and matrix[row][column]:
                matrix[row] = [a ^ b for a, b in zip(matrix[row], matrix[column])]
                operations.append(("cx", column, row))

    return tuple(operations)


# Aplica MixColumns ou a sua inversa através de portas reversíveis
def apply_mix_columns(circuit, state_qubits, inverse=False):
    columns = [state_qubits[8:12] + state_qubits[12:16], state_qubits[0:4] + state_qubits[4:8]]
    operations = get_mix_columns_operations()
    for column in columns:
        # A inversa corresponde à sequência inversa de operações
        sequence = operations if inverse else reversed(operations)

        for operation, first, second in sequence:
            if operation == "swap":
                circuit.swap(column[first], column[second])
            else:
                circuit.cx(column[first], column[second])

# Executa a encriptação S-AES ou a desencriptação reversível
def apply_s_aes_encryption(circuit, state_qubits, schedule_qubits, inverse=False):
    if inverse:
        # Inverter a segunda ronda
        apply_add_round_key(circuit, state_qubits, schedule_qubits)

        apply_shift_rows(circuit, state_qubits)
        apply_sub_nibbles(circuit, state_qubits, inverse=True)

        # Recuperar a segunda subchave
        apply_key_schedule_round(circuit, schedule_qubits, 0x30, inverse=True)

        apply_add_round_key(circuit, state_qubits, schedule_qubits)

        # Inverter a primeira ronda
        apply_mix_columns(circuit, state_qubits, inverse=True)

        apply_shift_rows(circuit, state_qubits)

        apply_sub_nibbles(circuit, state_qubits, inverse=True)

        # Recuperar a chave original
        apply_key_schedule_round(circuit, schedule_qubits, 0x80, inverse=True)

        apply_add_round_key(circuit, state_qubits, schedule_qubits)
    else:
        # Chave inicial
        apply_add_round_key(circuit, state_qubits, schedule_qubits)
        # Primeira ronda
        apply_sub_nibbles(circuit, state_qubits)
        apply_shift_rows(circuit, state_qubits)
        apply_mix_columns(circuit, state_qubits)

        # Gerar e aplicar a primeira subchave
        apply_key_schedule_round(circuit, schedule_qubits, 0x80)

        apply_add_round_key(circuit, state_qubits, schedule_qubits)

        # Gerar a segunda subchave
        apply_key_schedule_round(circuit, schedule_qubits, 0x30)

        # Segunda ronda
        apply_sub_nibbles(circuit, state_qubits)
        apply_shift_rows(circuit, state_qubits)

        apply_add_round_key(circuit, state_qubits, schedule_qubits)


# Marca com uma fase negativa o estado correspondente ao ciphertext esperado
def apply_ciphertext_phase_mark(circuit, state_qubits, ciphertext):
    # Inverter os bits que são zero no ciphertext
    for bit in range(16):
        if ((ciphertext >> bit) & 1) == 0:
            circuit.x(state_qubits[bit])

    # Inverter a fase apenas quando os 16 qubits estão em |1>
    circuit.mcp(np.pi, state_qubits[:-1], state_qubits[-1])
    # Restaurar os bits alterados
    for bit in range(16):
        if ((ciphertext >> bit) & 1) == 0:
            circuit.x(state_qubits[bit])



# Executa a cifra S-AES, marca o ciphertext e limpa os registos auxiliares
def apply_s_aes_phase_oracle(circuit, key_qubits, state_qubits, schedule_qubits, ciphertext,fixed_key_bits):
    # Inicializar diretamente os bits fixos da chave no registo auxiliar
    for bit in range(16):
        if (fixed_key_bits >> bit) & 1:
            circuit.x(schedule_qubits[bit])

    # Copiar apenas os bits variáveis da chave
    for bit, key_qubit in enumerate(key_qubits):
        circuit.cx(key_qubit, schedule_qubits[bit])
    # Executar a encriptação S-AES
    apply_s_aes_encryption(circuit, state_qubits, schedule_qubits)
    # Marcar o ciphertext correto
    apply_ciphertext_phase_mark(circuit,state_qubits, ciphertext)

    # Desfazer a encriptação
    apply_s_aes_encryption(circuit, state_qubits, schedule_qubits, inverse=True)

    # Limpar os bits variáveis do registo auxiliar
    for bit, key_qubit in enumerate(key_qubits):
        circuit.cx(key_qubit, schedule_qubits[bit])

    # Limpar os bits fixos do registo auxiliar
    for bit in range(16):
        if (fixed_key_bits >> bit) & 1:
            circuit.x(schedule_qubits[bit])

# Constrói o operador de difusão de Grover
def build_diffuser(n_bits):
    if n_bits < 2:
        raise ValueError("São necessários pelo menos 2 qubits.")

    diffuser = QuantumCircuit(n_bits)
    diffuser.h(range(n_bits))
    diffuser.x(range(n_bits))
    diffuser.h(n_bits - 1)
    diffuser.mcx(list(range(n_bits - 1)), n_bits - 1)
    diffuser.h(n_bits - 1)

    diffuser.x(range(n_bits))
    diffuser.h(range(n_bits))

    return diffuser

# Constrói o circuito de Grover com apenas os bits variáveis da chave
def build_grover_circuit(n_bits, plaintext, ciphertext, fixed_key_bits, iterations):
    if not 2 <= n_bits <= 16:
        raise ValueError("O número de bits variáveis deve estar entre 2 e 16.")

    if not 0 <= plaintext <= 0xFFFF:
        raise ValueError("O plaintext deve ter 16 bits.")

    if not 0 <= ciphertext <= 0xFFFF:
        raise ValueError("O ciphertext deve ter 16 bits.")

    if not 0 <= fixed_key_bits <= 0xFFFF:
        raise ValueError("Os bits fixos devem ter 16 bits.")

    variable_mask = (1 << n_bits) - 1

    if fixed_key_bits & variable_mask:
        raise ValueError("Os bits variáveis devem começar a zero.")

    if iterations < 0:
        raise ValueError("O número de iterações não pode ser negativo.")

    # Utilizar apenas n_bits para a pesquisa e 32 qubits auxiliares
    circuit = QuantumCircuit(n_bits + 32, n_bits)

    key_qubits = list(range(n_bits))
    state_qubits = list(range(n_bits, n_bits + 16))
    schedule_qubits = list(range(n_bits + 16, n_bits + 32))

    # Preparar superposição uniforme
    circuit.h(key_qubits)

    # Inicializar o plaintext
    for bit in range(16):
        if (plaintext >> bit) & 1:
            circuit.x(state_qubits[bit])

    # Preparar o operador de difusão
    diffuser = build_diffuser(n_bits)

    # Aplicar as iterações de Grover
    for _ in range(iterations):
        apply_s_aes_phase_oracle(circuit,key_qubits, state_qubits, schedule_qubits, ciphertext, fixed_key_bits)
        circuit.compose(diffuser, qubits=key_qubits, inplace=True)

    # Medir apenas os bits variáveis
    circuit.measure(key_qubits, range(n_bits))

    return circuit

# Constrói um circuito de teste para validar a encriptação S-AES
def build_s_aes_encryption_test_circuit(plaintext, key):
    # Só precisamos do estado e do registo auxiliar da chave
    circuit = QuantumCircuit(32, 16)

    state_qubits = list(range(16))
    schedule_qubits = list(range(16, 32))

    # Inicializar a chave no registo auxiliar
    for bit in range(16):
        if (key >> bit) & 1:
            circuit.x(schedule_qubits[bit])

    # Inicializar o plaintext
    for bit in range(16):
        if (plaintext >> bit) & 1:
            circuit.x(state_qubits[bit])

    # Executar a encriptação
    apply_s_aes_encryption(circuit, state_qubits, schedule_qubits)

    # Medir o ciphertext
    circuit.measure(state_qubits, range(16))

    return circuit
