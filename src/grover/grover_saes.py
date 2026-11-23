from qiskit import QuantumCircuit
from qiskit.circuit.library import DiagonalGate

# Constrói um oráculo que marca as chaves válidas.
def build_phase_oracle(n_bits, marked_states):
    dimension = 1 << n_bits
    diagonal = [1.0 + 0j] * dimension

    if not marked_states:
        raise ValueError("É necessário indicar pelo menos um estado válido.")

    for state in marked_states:
        if not 0 <= state < dimension:
            raise ValueError("Estado marcado inválido.")

        diagonal[state] = -1.0 + 0j

    oracle = QuantumCircuit(n_bits, name="Oraculo S-AES")
    oracle.append(DiagonalGate(diagonal), range(n_bits))

    return oracle


# Constrói o operador de difusão de Grover.
def build_diffuser(n_bits):
    if n_bits < 2:
        raise ValueError("São necessários pelo menos 2 qubits.")

    diffuser = QuantumCircuit(n_bits, name="Diffuser")

    diffuser.h(range(n_bits))
    diffuser.x(range(n_bits))

    diffuser.h(n_bits - 1)
    diffuser.mcx(list(range(n_bits - 1)), n_bits - 1)
    diffuser.h(n_bits - 1)

    diffuser.x(range(n_bits))
    diffuser.h(range(n_bits))

    return diffuser


# Constrói o circuito completo de Grover
def build_grover_circuit(n_bits, marked_states, iterations):
    if iterations < 0:
        raise ValueError("O número de iterações não pode ser negativo.")

    oracle = build_phase_oracle(n_bits, marked_states)
    diffuser = build_diffuser(n_bits)
    circuit = QuantumCircuit(n_bits, n_bits)

    # Preparar superposição uniforme
    circuit.h(range(n_bits))

    # Aplicar o operador de Grover
    for _ in range(iterations):
        circuit.compose(oracle, inplace=True)
        circuit.compose(diffuser, inplace=True)

    # Medir
    circuit.measure(range(n_bits), range(n_bits))

    return circuit
