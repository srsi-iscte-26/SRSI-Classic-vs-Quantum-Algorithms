import os
import csv
import math
import matplotlib.pyplot as plt

from qiskit import transpile
from qiskit_aer import AerSimulator
from src.classical.saes import encrypt
from src.classical.brute_force import brute_force_search
from src.grover.grover_saes import build_grover_circuit

PLAINTEXT = 0xD728
SECRET_KEY = 0x4AF5
SEARCH_SIZES = (4, 8, 12)
SHOTS = 2048
SEED = 42

os.makedirs("results", exist_ok=True)
os.makedirs("plots", exist_ok=True)


simulator = AerSimulator()
measurement_results = []
summary_results = []

# -------------------------
# Execução das experiências
# -------------------------

CIPHERTEXT = encrypt(PLAINTEXT, SECRET_KEY)

print(f"Texto original: {PLAINTEXT:04X}")
print(f"Texto cifrado:  {CIPHERTEXT:04X}")


for n_bits in SEARCH_SIZES:
    print("\n" + "=" * 45)
    print(f"ESPAÇO DE PESQUISA: {n_bits} BITS")
    print("=" * 45)

    # Determinar os bits fixos e variáveis da chave
    variable_mask = (1 << n_bits) - 1
    fixed_key_bits = SECRET_KEY & (0xFFFF ^ variable_mask)

    # Executar a pesquisa clássica
    matches, classical_attempts = brute_force_search(plaintext=PLAINTEXT, ciphertext=CIPHERTEXT, n_bits=n_bits, fixed_key_bits=fixed_key_bits)

    # Converter as chaves válidas nos estados dos qubits
    marked_states = [key & variable_mask for key in matches]

    if not marked_states:
        raise RuntimeError("Não foi encontrada nenhuma chave válida.")

    # Calcular o número ótimo de iterações
    N = 2 ** n_bits
    M = len(marked_states)

    theta = math.asin(math.sqrt(M / N))
    optimal_iterations = round(math.pi / (4 * theta) - 0.5)
    theoretical_probability = math.sin((2 * optimal_iterations + 1) * theta) ** 2

    # Selecionar algumas iterações para testar
    iterations_to_test = sorted(set([
        0,
        1,
        max(0, optimal_iterations // 2),
        max(0, optimal_iterations - 1),
        optimal_iterations,
        optimal_iterations + 1
    ]))

    circuits = [build_grover_circuit(n_bits=n_bits, marked_states=marked_states, iterations=iteration) for iteration in iterations_to_test]

    # Preparar os circuitos para o simulador
    compiled_circuits = transpile(circuits, simulator, seed_transpiler=SEED)

    # Executar as experiências
    result = simulator.run(compiled_circuits, shots=SHOTS, seed_simulator=SEED).result()

    # Recolher os resultados das medições
    experimental_probabilities = {}
    for index, iteration in enumerate(iterations_to_test):
        counts = result.get_counts(index)
        successful_shots = 0
        for bitstring, count in counts.items():
            state = int(bitstring.replace(" ", ""), 2)
            if state in marked_states:
                successful_shots += count

        probability = successful_shots / SHOTS
        experimental_probabilities[iteration] = probability

        theoretical = math.sin((2 * iteration + 1) * theta) ** 2

        measurement_results.append({
            "bits_variaveis": n_bits,
            "iteracoes": iteration,
            "medicoes": SHOTS,
            "medicoes_bem_sucedidas": successful_shots,
            "probabilidade_experimental": probability,
            "probabilidade_teorica": theoretical
        })

        print(f"Iterações: {iteration:3d} | "f"Experimental: {probability:.4f} | "f"Teórica: {theoretical:.4f}")

    # Recolher métricas do circuito com número ótimo de iterações
    optimal_index = iterations_to_test.index(optimal_iterations)
    optimal_circuit = compiled_circuits[optimal_index]
    optimal_experimental_probability = (experimental_probabilities[optimal_iterations])

    summary = {
        "bits_variaveis": n_bits,
        "espaco_pesquisa": N,
        "chaves_validas": M,
        "bits_fixos": f"{fixed_key_bits:04X}",
        "tentativas_classicas": classical_attempts,
        "iteracoes_otimas": optimal_iterations,
        "probabilidade_teorica": theoretical_probability,
        "probabilidade_experimental": optimal_experimental_probability,
        "medicoes": SHOTS,
        "qubits": optimal_circuit.num_qubits,
        "profundidade": optimal_circuit.depth(),
        "operacoes": optimal_circuit.size()
    }

    summary_results.append(summary)

    # -----------------------
    # Construção do gráfico
    # -----------------------

    max_iterations = 2 * optimal_iterations

    theoretical_iterations = list(range(max_iterations + 1))
    theoretical_curve = [math.sin((2 * iteration + 1) * theta) ** 2 for iteration in theoretical_iterations]

    experimental_iterations = list(experimental_probabilities.keys())
    experimental_curve = [experimental_probabilities[iteration] for iteration in experimental_iterations]

    plt.figure(figsize=(9, 5))
    plt.plot(theoretical_iterations, theoretical_curve, label="Probabilidade teórica")
    plt.scatter(experimental_iterations, experimental_curve, label="Probabilidade experimental")
    plt.axvline(optimal_iterations, linestyle="--", label="Número ótimo de iterações")
    plt.xlabel("Iterações de Grover")
    plt.ylabel("Probabilidade de sucesso")
    plt.title(f"Pesquisa de Grover - {n_bits} bits variáveis")
    plt.ylim(0, 1.05)
    plt.legend()
    plt.grid(True)
    plt.tight_layout()
    plt.savefig(f"plots/grover_{n_bits}_bits.png", dpi=150)
    plt.close()

# -----------------------------
# Guardar os resultados em csv
# ------------------------------

with open(
    "results/grover_measurements.csv",
    "w",
    newline="",
    encoding="utf-8"
) as file:

    writer = csv.DictWriter(
        file,
        fieldnames=measurement_results[0].keys()
    )

    writer.writeheader()
    writer.writerows(measurement_results)


with open(
    "results/grover_summary.csv",
    "w",
    newline="",
    encoding="utf-8"
) as file:

    writer = csv.DictWriter(
        file,
        fieldnames=summary_results[0].keys()
    )

    writer.writeheader()
    writer.writerows(summary_results)


# -----------------------------
# Resumo
# -----------------------------

print("\n" + "=" * 55)
print("RESUMO FINAL DAS EXPERIÊNCIAS DE GROVER")
print("=" * 55)

for item in summary_results:

    print(f"\nBits variáveis: {item['bits_variaveis']}")
    print(f"Tentativas clássicas: {item['tentativas_classicas']}")
    print(f"Iterações ótimas: {item['iteracoes_otimas']}")

    print(
        f"Probabilidade teórica: "
        f"{item['probabilidade_teorica']:.4f}"
    )

    print(
        f"Probabilidade experimental: "
        f"{item['probabilidade_experimental']:.4f}"
    )

    print(f"Qubits: {item['qubits']}")
    print(f"Profundidade: {item['profundidade']}")
    print(f"Número de operações: {item['operacoes']}")

print("\nResultados guardados em:")
print("  results/grover_measurements.csv")
print("  results/grover_summary.csv")
print("  plots/")
