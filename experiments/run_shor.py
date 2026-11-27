import os
import time
from collections import Counter
from fractions import Fraction
import matplotlib.pyplot as plt
import pandas as pd
from qiskit import transpile
from qiskit_aer import AerSimulator
from src.shor.shor import (build_order_finding_circuit, recover_order, factor_from_order)
from src.classical.factoring import factorize_classically

# --------------------------------------------------
# Configuração
# --------------------------------------------------

EXPERIMENTS = [
    {"N": 15, "A": 7},
    {"N": 21, "A": 2}
]

N_COUNTING_QUBITS = 8
SHOTS = 2048
SEED = 42

os.makedirs("results", exist_ok=True)
os.makedirs("plots", exist_ok=True)

# --------------------------------------------------
# SIMULADOR
# --------------------------------------------------

simulator = AerSimulator(method="statevector")
measurement_results = []
summary_results = []

# --------------------------------------------------
# EXECUÇÃO DAS EXPERIÊNCIAS
# --------------------------------------------------

for experiment in EXPERIMENTS:
    N = experiment["N"]
    A = experiment["A"]

    print("\n" + "=" * 55)
    print(f"EXPERIÊNCIA DE SHOR: N = {N}, BASE = {A}")
    print("=" * 55)

    if N % 2 == 0:
        raise ValueError("O número deve ser ímpar.")
    if __import__("math").gcd(A, N) != 1:
        raise ValueError("A base e o número devem ser coprimos.")

    # Construir o circuito
    circuit = build_order_finding_circuit(modulus=N, base=A, n_counting_qubits=N_COUNTING_QUBITS)

    # Preparar o circuito para o simulador
    compiled_circuit = transpile(circuit, simulator, seed_transpiler=SEED)

    # Executar o circuito e medir o tempo
    start_time = time.perf_counter()
    result = simulator.run(compiled_circuit, shots=SHOTS, seed_simulator=SEED).result()

    execution_time = time.perf_counter() - start_time
    counts = result.get_counts(compiled_circuit)
    period_counts = Counter()
    factor_counts = Counter()

    print("\nDistribuição das fases medidas:")

    # Converter as medições para valores inteiros
    counts_by_state = {int(bitstring.replace(" ", ""), 2): count for bitstring, count in counts.items()}

    # Analisar todos os estados possíveis
    for measured_value in range(1 << N_COUNTING_QUBITS):
        count = counts_by_state.get(measured_value, 0)
        phase = Fraction(measured_value, 1 << N_COUNTING_QUBITS).limit_denominator(N)

        # Recuperar o período
        order = recover_order(measured_value, N_COUNTING_QUBITS, A, N)

        # Recuperar os fatores
        factors = factor_from_order(N, A, order)

        # Contabilizar os resultados válidos
        if count > 0 and order is not None:
            period_counts[order] += count
        if count > 0 and factors is not None:
            factor_counts[factors] += count
        # Mostrar apenas estados efetivamente medidos
        if count > 0:

            period_text = (str(order) if order is not None else "Não encontrado")
            factors_text = (str(factors) if factors is not None else "Não encontrados")

            print(
                f"Estado: {measured_value:08b} | "
                f"Fração: {phase} | "
                f"Período: {period_text} | "
                f"Fatores: {factors_text} | "
                f"Ocorrências: {count}"
            )

        # Guardar a distribuição completa
        measurement_results.append({
            "numero": N,
            "base": A,
            "estado_medido": f"{measured_value:08b}",
            "valor_decimal": measured_value,
            "fase": str(phase),
            "ocorrencias": count,
            "periodo": order,
            "fator_1": factors[0] if factors else None,
            "fator_2": factors[1] if factors else None
        })

    # Determinar o resultado mais frequente
    successful_shots = sum(factor_counts.values())

    if factor_counts:
        best_factors = factor_counts.most_common(1)[0][0]
        best_period = period_counts.most_common(1)[0][0]
        factor1, factor2 = best_factors
    else:
        best_factors = None
        best_period = None
        factor1 = None
        factor2 = None

    # Fatorização clássica
    classical_factor1, classical_factor2, classical_attempts = (factorize_classically(N))

    # Recolher métricas
    summary = {
        "numero": N,
        "base": A,
        "periodo": best_period,
        "fator_1": factor1,
        "fator_2": factor2,
        "medicoes": SHOTS,
        "medicoes_validas": successful_shots,
        "taxa_sucesso": successful_shots / SHOTS,
        "fator_1_classico": classical_factor1,
        "fator_2_classico": classical_factor2,
        "tentativas_classicas": classical_attempts,
        "qubits": compiled_circuit.num_qubits,
        "profundidade": compiled_circuit.depth(),
        "operacoes": compiled_circuit.size(),
        "tempo_execucao_segundos": execution_time
    }

    summary_results.append(summary)

    # Apresentar o resumo da experiência
    print("\nResultados da fatorização:")
    print(f"Período: {best_period}")
    print(f"Fatores: {best_factors}")
    print(
        f"Verificação: {factor1} x {factor2} = "
        f"{factor1 * factor2}" if best_factors else
        "Não foi possível fatorizar o número."
    )

    print(
        f"Medições que produziram fatores: "
        f"{successful_shots}/{SHOTS}"
    )

    print("\nFatorização clássica:")
    print(f"Fatores: {classical_factor1} e {classical_factor2}")
    print(f"Divisores testados: {classical_attempts}")

    print("\nMétricas do circuito:")
    print(f"Qubits: {compiled_circuit.num_qubits}")
    print(f"Profundidade: {compiled_circuit.depth()}")
    print(f"Operações: {compiled_circuit.size()}")
    print(f"Tempo de execução: {execution_time:.4f} segundos")


# --------------------------------------------------
# GUARDAR OS RESULTADOS EM CSV
# --------------------------------------------------

pd.DataFrame(measurement_results).to_csv(
    "results/shor_measurements.csv",
    index=False,
    encoding="utf-8"
)

pd.DataFrame(summary_results).to_csv(
    "results/shor_summary.csv",
    index=False,
    encoding="utf-8"
)


# --------------------------------------------------
# COMPARAÇÃO DOS RECURSOS COMPUTACIONAIS
# --------------------------------------------------

summary_df = pd.DataFrame(summary_results)
labels = [f"N = {number}" for number in summary_df["numero"]]
fig, axes = plt.subplots(1, 3, figsize=(13, 4))

# Comparar o número de qubits
axes[0].bar(labels, summary_df["qubits"])
axes[0].set_title("Número de qubits")
axes[0].set_ylabel("Qubits")

# Comparar a profundidade
axes[1].bar(labels, summary_df["profundidade"])
axes[1].set_title("Profundidade dos circuitos")
axes[1].set_ylabel("Profundidade")

# Comparar o número de operações
axes[2].bar(labels, summary_df["operacoes"])
axes[2].set_title("Número de operações")
axes[2].set_ylabel("Operações")

for axis in axes:
    axis.grid(axis="y", alpha=0.3)

fig.suptitle("Comparação dos recursos computacionais de Shor")

plt.tight_layout()
plt.savefig("plots/shor_resources_comparison.png", dpi=150)
plt.close()


# --------------------------------------------------
# RESUMO FINAL
# --------------------------------------------------

print("\n" + "=" * 55)
print("COMPARAÇÃO FINAL DAS EXPERIÊNCIAS DE SHOR")
print("=" * 55)

print(
    summary_df[
        [
            "numero",
            "periodo",
            "fator_1",
            "fator_2",
            "taxa_sucesso",
            "qubits",
            "profundidade",
            "operacoes"
        ]
    ].to_string(index=False)
)

print("\nResultados guardados:")
print("  results/shor_measurements.csv")
print("  results/shor_summary.csv")
print("  plots/shor_resources_comparison.png")
