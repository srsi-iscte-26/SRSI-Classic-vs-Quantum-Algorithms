# O Impacto da Computação Quântica na Segurança dos Sistemas Criptográficos Clássicos: Análise dos Algoritmos de Shor e Grover sobre o RSA e o AES

Projeto de grupo da unidade curricular **Segurança em Redes e Sistemas de Informação (SRSI)**, ISCTE, 2026/2027.

Docentes: Prof. Valderi Reis Quietinho Leithardt e Prof. Maurício Machado da Rosa

| Nome | N.º |
|---|---|
| Francisco Lopes | 111358 |
| Francisco Peixoto | 111270 |
| Inês Batista | 142875 |
| Raul Azevedo | 111479 |

# Descrição do Projeto 

Análise comparativa de algoritmos criptográficos clássicos e quânticos, com foco no impacto da computação quântica no RSA e no AES.

## Implementações

- S-AES clássico 
- Algoritmo de Grover aplicado ao S-AES
- Algoritmo de Shor aplicado à fatorização de inteiros pequenos

## Tecnologias 

- Python
- Qiskit
- Qiskit Aer
- NumPy
- Pandas
- Matplotlib

## Estrutura

- `src/`: Implementações dos algoritmos
- `experiments/`: Scripts de execução experimental
- `results/`: Resultados experimentais
- `plots/`: Gráficos gerados
- `report/`: Relatório em pdf e latex da componente teórica do projeto

## Instalação

1. **Criar o ambiente virtual:**
   ```bash
   python -m venv .venv
   ```
2. **Ativar o ambiente virtual:**
   - **Windows (Git Bash):**
    ```bash
    source .venv/Scripts/activate
    ```
   - **Windows (PowerShell):**
    ```powershell
    .\.venv\Scripts\Activate.ps1
    ```
   - **Windows (Command Prompt / CMD):**
    ```cmd
    .venv\Scripts\activate.bat
    ```
   - **Linux / macOS:**
    ```bash
    source .venv/bin/activate
    ```
3. **Instalar as dependências:**
   ```bash
   pip install -r requirements.txt
   ```


    




