import math


# Fatoriza um número através de pesquisa por divisores
def factorize_classically(number):
    if number < 4:
        raise ValueError("O número deve ser igual ou superior a 4.")
    attempts = 0

    # Testar possíveis divisores até à raiz quadrada do número
    for divisor in range(2, math.isqrt(number) + 1):
        attempts += 1
        if number % divisor == 0:
            return divisor, number // divisor, attempts

    raise ValueError("O número não possui fatores não triviais.")
