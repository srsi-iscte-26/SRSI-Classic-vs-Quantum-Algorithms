
import math
import numpy as np

from fractions import Fraction
from qiskit import QuantumCircuit
from qiskit.circuit.library import UnitaryGate


# Constrói a operação quântica de multiplicação modular
def build_modular_multiplication_gate(multiplier, modulus):

    n_work = (modulus - 1).bit_length()
    dimension = 1 << n_work

    multiplier %= modulus

    if math.gcd(multiplier, modulus) != 1:
        raise ValueError("O multiplicador e o módulo devem ser coprimos.")

    matrix = np.zeros((dimension, dimension), dtype=complex)

    for value in range(dimension):

        # Os valores inferiores ao módulo são multiplicados modularmente
        if value < modulus:
            output_value = (multiplier * value) % modulus

        # Os restantes estados permanecem inalterados
        else:
            output_value = value

        matrix[output_value, value] = 1.0

    return UnitaryGate(
        matrix,
        label=f"Mult. x{multiplier} mod {modulus}"
    )


# Aplica a transformada de Fourier quântica inversa
def apply_inverse_qft(circuit, qubits):

    n = len(qubits)

    # Inverter a ordem dos qubits
    for i in range(n // 2):
        circuit.swap(qubits[i], qubits[n - 1 - i])

    # Aplicar as rotações de fase inversas e as portas Hadamard
    for j in range(n):

        for k in range(j):
            angle = -math.pi / (2 ** (j - k))
            circuit.cp(angle, qubits[k], qubits[j])

        circuit.h(qubits[j])


# Constrói o circuito de estimativa de fase para encontrar o período
def build_order_finding_circuit(modulus, base, n_counting_qubits=8):

    if math.gcd(base, modulus) != 1:
        raise ValueError("A base e o módulo devem ser coprimos.")

    n_work = (modulus - 1).bit_length()

    circuit = QuantumCircuit(
        n_counting_qubits + n_work,
        n_counting_qubits
    )

    counting_qubits = list(range(n_counting_qubits))

    work_qubits = list(
        range(n_counting_qubits, n_counting_qubits + n_work)
    )

    # Inicializar o registo de trabalho no estado |1>
    circuit.x(work_qubits[0])

    # Preparar superposição uniforme no registo de controlo
    circuit.h(counting_qubits)

    # Aplicar as multiplicações modulares controladas
    for j, control_qubit in enumerate(counting_qubits):

        exponent = 1 << j
        multiplier = pow(base, exponent, modulus)

        # Não é necessário aplicar operações identidade
        if multiplier == 1:
            continue

        multiplication_gate = build_modular_multiplication_gate(
            multiplier,
            modulus
        )

        controlled_gate = multiplication_gate.control()

        circuit.append(
            controlled_gate,
            [control_qubit] + work_qubits
        )

    # Aplicar a transformada de Fourier inversa
    apply_inverse_qft(circuit, counting_qubits)

    # Medir o registo de controlo
    circuit.measure(counting_qubits, range(n_counting_qubits))

    return circuit



# Recupera o menor período através de frações contínuas
def recover_order(measured_value, n_counting_qubits, base, modulus):
    if measured_value == 0:
        return None

    # Aproximar a fase medida utilizando frações contínuas
    phase = Fraction(measured_value, 1 << n_counting_qubits).limit_denominator(modulus)
    denominator = phase.denominator
    if phase.numerator == 0 or denominator == 1:
        return None

    # Procurar múltiplos do denominador que satisfaçam a condição modular
    for candidate in range(denominator, modulus + 1, denominator):
        if pow(base, candidate, modulus) == 1:
            # Encontrar o menor período que satisfaz a condição
            for order in range(1, candidate + 1):
                if (candidate % order == 0 and pow(base, order, modulus) == 1):
                    # Confirmar que o denominador divide o período encontrado
                    if order % denominator == 0:
                        return order

                    return None
    return None


# Calcula os fatores do número a partir do período encontrado
def factor_from_order(modulus, base, order):

    if order is None or order % 2 != 0:
        return None

    x = pow(base, order // 2, modulus)

    # Verificar se a solução permite obter fatores não triviais
    if x == 1 or x == modulus - 1:
        return None

    factor1 = math.gcd(x - 1, modulus)
    factor2 = math.gcd(x + 1, modulus)

    if factor1 in (1, modulus) or factor2 in (1, modulus):
        return None

    return tuple(sorted((factor1, factor2)))
