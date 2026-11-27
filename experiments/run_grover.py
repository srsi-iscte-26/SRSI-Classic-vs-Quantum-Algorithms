import csv
import os
import matplotlib.pyplot as plt
import math
from qiskit import transpile
from qiskit_aer import AerSimulator
from src.classical.saes import encrypt
from src.grover.grover_saes import (build_s_aes_encryption_test_circuit, build_grover_circuit)

# -----------------
# Configuração
# -----------------

PLAINTEXT = 0xD728
SECRET_KEY = 0x4AF5
N_BITS = 4
SHOTS = 512
SEED = 42

FILE_PREFIX = f"grover_reversivel_{N_BITS}_bits"

# --------------------------------------------------
# PREPARAÇÃO DOS DADOS
# --------------------------------------------------

CIPHERTEXT = encrypt(PLAINTEXT, SECRET_KEY)
VARIABLE_MASK = (1 << N_BITS) - 1
FIXED_KEY_BITS = SECRET_KEY & (0xFFFF ^ VARIABLE_MASK)
EXPECTED_STATE = SECRET_KEY & VARIABLE_MASK

N_VALID_KEYS = 1
N_STATES = 1 << N_BITS

THETA = math.asin(math.sqrt(N_VALID_KEYS / N_STATES))
OPTIMAL_ITERATIONS = round(math.pi / (4 * THETA) - 0.5)
THEORETICAL_PROBABILITY = math.sin((2 * OPTIMAL_ITERATIONS + 1) * THETA) ** 2


print("=" * 50)
print("CONFIGURAÇÃO DA EXPERIÊNCIA")
print("=" * 50)

print(f"Texto original: {PLAINTEXT:04X}")
print(f"Texto cifrado: {CIPHERTEXT:04X}")
print(f"Bits variáveis: {N_BITS}")
print(f"Bits fixos: {FIXED_KEY_BITS:04X}")
print(f"Espaço de pesquisa: {N_STATES}")
print(f"Iterações de Grover: {OPTIMAL_ITERATIONS}")

# -----------
# SIMULADOR
# ------------

simulator = AerSimulator(method="matrix_product_state")

# ---------------------------------------
# Validação da encriptação S-AES Quântica
# ---------------------------------------

print("\n" + "=" * 50)
print("Validação da encriptação S-AES Quântica")
print("=" * 50)

test_circuit = build_s_aes_encryption_test_circuit(PLAINTEXT, SECRET_KEY)

compiled_test = transpile(test_circuit, simulator, optimization_level=1, seed_transpiler=SEED)
test_result = simulator.run(compiled_test, shots=1, seed_simulator=SEED).result()
test_counts = test_result.get_counts(compiled_test)
measured_state = int(next(iter(test_counts)).replace(" ", ""), 2)

print(f"Ciphertext clássico: {CIPHERTEXT:04X}")
print(f"Ciphertext quântico: {measured_state:04X}")

if measured_state != CIPHERTEXT:
    raise RuntimeError("A encriptação S-AES quântica não corresponde à versão clássica.")

print("Encriptação S-AES quântica validada!")

# ---------------------------------
# Construção do circuito de grover
# ---------------------------------

print("\n" + "=" * 50)
print("CONSTRUÇÃO DO CIRCUITO DE GROVER")
print("=" * 50)

circuit = build_grover_circuit(n_bits=N_BITS, plaintext=PLAINTEXT, ciphertext=CIPHERTEXT, fixed_key_bits=FIXED_KEY_BITS, iterations=OPTIMAL_ITERATIONS)

print(f"Qubits totais: {circuit.num_qubits}")
print(f"Qubits de pesquisa: {N_BITS}")

# --------------------------------------------------
# TRANSPILAÇÃO E EXECUÇÃO
# --------------------------------------------------

compiled_circuit = transpile(circuit, simulator, optimization_level=1, seed_transpiler=SEED)

print("\nA executar o circuito no simulador Aer...")

result = simulator.run(compiled_circuit, shots=SHOTS, seed_simulator=SEED).result()
counts = result.get_counts(compiled_circuit)

# ----------------------
# Análise das Medições
# ----------------------

successful_shots = 0

print("\n" + "=" * 50)
print("Resultados das Medições:")
print("=" * 50)

for bitstring, count in sorted(counts.items(), key=lambda item: int(item[0].replace(" ", ""), 2)):
    state = int(bitstring.replace(" ", ""), 2)
    print(f"{bitstring}: {count}")
    if state == EXPECTED_STATE:
        successful_shots += count

EXPERIMENTAL_PROBABILITY = successful_shots / SHOTS

# ------------------
# Resultados Finais
# -------------------

print("\n" + "=" * 50)
print("Resultados Finais")
print("=" * 50)

print(f"Estado esperado: {EXPECTED_STATE:0{N_BITS}b}")
print(f"Iterações de Grover: {OPTIMAL_ITERATIONS}")
print(f"Medições: {SHOTS}")
print(f"Medições bem-sucedidas: {successful_shots}")

print(f"Probabilidade experimental: "f"{EXPERIMENTAL_PROBABILITY:.4f}")

print(f"Probabilidade teórica: "f"{THEORETICAL_PROBABILITY:.4f}")

# ----------------------
# Métricas do circuito
# ----------------------

print("\n" + "=" * 50)
print("Métricas do circuito")
print("=" * 50)

print(f"Qubits totais: {compiled_circuit.num_qubits}")
print(f"Qubits de pesquisa: {N_BITS}")
print(f"Profundidade: {compiled_circuit.depth()}")
print(f"Número de operações: {compiled_circuit.size()}")
print(f"Operações por tipo: {compiled_circuit.count_ops()}")


# --------------------------------------------------
# GUARDAR OS RESULTADOS
# --------------------------------------------------

os.makedirs("results", exist_ok=True)
os.makedirs("plots", exist_ok=True)

# Organizar as contagens das medições
counts_by_state = {
    int(bitstring.replace(" ", ""), 2): count
    for bitstring, count in counts.items()
}

# Guardar a distribuição dos 16 estados possíveis
with open(
    "results/grover_reversivel_4_bits_counts.csv",
    "w",
    newline="",
    encoding="utf-8"
) as file:

    writer = csv.DictWriter(
        file,
        fieldnames=[
            "estado_binario",
            "estado_decimal",
            "chave_candidata",
            "contagem",
            "chave_correta"
        ]
    )

    writer.writeheader()

    for state in range(N_STATES):

        writer.writerow({
            "estado_binario": f"{state:04b}",
            "estado_decimal": state,
            "chave_candidata": f"0x{FIXED_KEY_BITS | state:04X}",
            "contagem": counts_by_state.get(state, 0),
            "chave_correta": state == EXPECTED_STATE
        })


# Guardar o resumo da experiência
with open("results/grover_reversivel_4_bits_summary.csv", "w", newline="", encoding="utf-8") as file:
    writer = csv.DictWriter(
        file,
        fieldnames=[
            "plaintext",
            "ciphertext",
            "bits_variaveis",
            "qubits_totais",
            "iteracoes",
            "medicoes",
            "medicoes_bem_sucedidas",
            "probabilidade_experimental",
            "probabilidade_teorica",
            "profundidade",
            "operacoes"
        ]
    )

    writer.writeheader()

    writer.writerow({
        "plaintext": f"{PLAINTEXT:04X}",
        "ciphertext": f"{CIPHERTEXT:04X}",
        "bits_variaveis": N_BITS,
        "qubits_totais": compiled_circuit.num_qubits,
        "iteracoes": OPTIMAL_ITERATIONS,
        "medicoes": SHOTS,
        "medicoes_bem_sucedidas": successful_shots,
        "probabilidade_experimental": EXPERIMENTAL_PROBABILITY,
        "probabilidade_teorica": THEORETICAL_PROBABILITY,
        "profundidade": compiled_circuit.depth(),
        "operacoes": compiled_circuit.size()
    })


# ---------------
# Gráfico
# ----------------

# Calcular a curva teórica para diferentes iterações
iterations_plot = range(9)
theoretical_curve = [math.sin((2 * iteration + 1) * THETA) ** 2 for iteration in iterations_plot]

plt.figure(figsize=(9, 5))
plt.plot(list(iterations_plot), theoretical_curve, label="Probabilidade teórica")
plt.scatter([OPTIMAL_ITERATIONS], [EXPERIMENTAL_PROBABILITY], label="Probabilidade experimental", zorder=3)
plt.axvline(OPTIMAL_ITERATIONS, linestyle="--", label="Iterações ótimas")
plt.xlabel("Iterações de Grover")
plt.ylabel("Probabilidade de sucesso")
plt.title("Grover com oráculo reversível S-AES - 4 bits")
plt.ylim(0, 1.05)
plt.xticks(list(iterations_plot))
plt.grid(True)
plt.legend()
plt.tight_layout()
plt.savefig("plots/grover_reversivel_4_bits.png", dpi=150)
plt.close()

print("\nResultados guardados:")
print("  results/grover_reversivel_4_bits_counts.csv")
print("  results/grover_reversivel_4_bits_summary.csv")
print("  plots/grover_reversivel_4_bits.png")