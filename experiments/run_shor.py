
from collections import Counter
from fractions import Fraction
import math

from qiskit import transpile
from qiskit_aer import AerSimulator
from src.shor.shor import (build_order_finding_circuit, recover_order, factor_from_order)
from src.classical.factoring import factorize_classically

N = 15
A = 7

N_COUNTING_QUBITS = 8
SHOTS = 2048

SEED = 42


# ---------------------------
# Construção do circuito
# ---------------------------

if math.gcd(A, N) != 1:
    raise ValueError("A base e o módulo devem ser coprimos.")

circuit = build_order_finding_circuit(
    modulus=N,
    base=A,
    n_counting_qubits=N_COUNTING_QUBITS
)


# ------------------------
# Execução no simulador
# ------------------------

simulator = AerSimulator(method="statevector")
compiled_circuit = transpile(circuit, simulator, seed_transpiler=SEED)
result = simulator.run(compiled_circuit,shots=SHOTS,seed_simulator=SEED).result()

counts = result.get_counts(compiled_circuit)

# --------------------------------------
# Recuperação do Período e dos Fatores
# --------------------------------------

period_counts = Counter()
factor_counts = Counter()

print(f"Número a fatorizar: {N}")
print(f"Base escolhida: {A}")

print("\nDistribuição das fases medidas:")

ordered_counts = sorted(counts.items(), key=lambda item: int(item[0].replace(" ", ""), 2))

for bitstring, count in ordered_counts:
    measured_value = int(bitstring.replace(" ", ""), 2)
    # Converter a medição numa aproximação da fase
    phase = Fraction(measured_value, 1 << N_COUNTING_QUBITS).limit_denominator(N)

    # Recuperar o período
    order = recover_order(measured_value, N_COUNTING_QUBITS, A, N)

    # Calcular os fatores
    factors = factor_from_order(N, A, order)

    period_text = str(order) if order is not None else "Não encontrado"

    factors_text = str(factors) if factors is not None else "Não encontrados"

    print(
        f"Estado: {bitstring.replace(' ', '')} | "
        f"Fração: {phase} | "
        f"Período: {period_text} | "
        f"Fatores: {factors_text} | "
        f"Ocorrências: {count}"
    )

    if order is not None:
        period_counts[order] += count

    if factors is not None:
        factor_counts[factors] += count


# --------------------------------------------------
# Resultados Fínais 
# --------------------------------------------------

print("\n" + "=" * 50)
print("Resultados da Fatorização")
print("=" * 50)

if not factor_counts:
    print("Não foi possível obter fatores não triviais.")
    print("Será necessário repetir a experiência.")
else:
    best_factors, successful_shots = factor_counts.most_common(1)[0]

    factor1, factor2 = best_factors

    print(f"Período mais frequente: {period_counts.most_common(1)[0][0]}")
    print(f"Fator 1: {factor1}")
    print(f"Fator 2: {factor2}")
    print(f"Verificação: {factor1} x {factor2} = {factor1 * factor2}")
    print(f"Medições que produziram fatores: {successful_shots}/{SHOTS}")


# --------------------------------------------------
# Métricas do circuito
# --------------------------------------------------

print("\n" + "=" * 50)
print("Métricas do Circuito")
print("=" * 50)

print(f"Qubits: {compiled_circuit.num_qubits}")
print(f"Profundidade: {compiled_circuit.depth()}")
print(f"Número de operações: {compiled_circuit.size()}")
print(f"Operações por tipo: {compiled_circuit.count_ops()}")


# --------------------------------------------------
# Comparação com a fatorização clássica
# --------------------------------------------------

classical_factor1, classical_factor2, classical_attempts = (factorize_classically(N))

print("\n" + "=" * 50)
print("Fatorização Clássica por Divisão de Tentativas")
print("=" * 50)

print(f"Número a fatorizar: {N}")
print(f"Fator 1: {classical_factor1}")
print(f"Fator 2: {classical_factor2}")
print(f"Divisores testados: {classical_attempts}")
print(f"Verificação: "f"{classical_factor1} x {classical_factor2} = "f"{classical_factor1 * classical_factor2}")