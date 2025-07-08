## Descrição

ProjetoK é um ambiente de testes de desempenho para servidores TCP implementados em Go e Python, com clientes também nessas linguagens. O objetivo é comparar o desempenho dos servidores sob diferentes cargas, utilizando automação de testes, análise estatística e geração de relatórios.

## Estrutura do Projeto

- `src/client/` — Clientes em Go (`client-go.go`) e Python (`client-python.py`).
- `src/server/` — Servidores em Go (`server-go.go`) e Python (`server-python.py`).
- `src/results/` — Resultados dos testes (CSVs, relatórios, gráficos).
- `src/tools/` — Scripts de análise de resultados e geração de gráficos.
- `scripts/` — Scripts de automação para rodar testes em lote (PowerShell e Bash).
- `docker/` — Dockerfiles para clientes e servidores.
- `kubernetes/` — YAMLs de deployment para rodar os servidores em cluster Kubernetes.

## Como rodar os testes

### Pré-requisitos
- Go 1.24+
- Python 3.11+
- PowerShell (Windows) ou Bash (Linux)
- Docker e Kubernetes (kind)

### Passos principais

1. **Instale as dependências Python:**
   ```powershell
   pip install -r requirements.txt
   ```

2. **Compile o cliente Go (opcional, o script faz isso automaticamente):**
   ```powershell
   go build -o src/client/client-go.exe src/client/client-go.go
   ```

3. **Execute o script de testes unificado:**
   ```powershell
   .\scripts\test-all.ps1
   ```
   Isso irá:
   - Criar/atualizar o cluster Kubernetes com kind
   - Fazer deploy dos servidores Go e Python
   - Rodar testes de carga com clientes Go e Python
   - Gerar arquivos CSV de resultados em `src/results/reports/`
   - Analisar os resultados e gerar relatórios estatísticos
   - Gerar gráficos comparativos automaticamente em `src/results/charts/`

4. **(Opcional) Rodar análise manual:**
   ```powershell
   python src/tools/analyze_results.py src/results/reports/test-go.csv go
   python src/tools/analyze_results.py src/results/reports/test-python.csv python
   ```
   ```powershell
   python src/tools/generate_charts.py
   ```
   Os gráficos serão salvos em `src/results/charts/`.

## Sobre os gráficos e métricas

- Os gráficos radar e tabelas comparativas são gerados automaticamente após os testes.
- As métricas analisadas incluem: Escalabilidade, Eficiência Relativa, Consistência (DPR), Tempo de Resposta por Mensagem, Speedup e Overhead.
- A explicação detalhada de cada métrica e suas unidades está disponível em `src/results/charts/README.md`.

## Como rodar manualmente um cliente

- **Go:**
  ```powershell
  .\src\client\client-go.exe <host> <porta> <num_msgs> <num_clientes> <cliente_id> <num_servidores> <rodada_id> <repeticao>
  ```
- **Python:**
  ```powershell
  python src/client/client-python.py <host> <porta> <num_msgs> <num_clientes> <cliente_id> <num_servidores> <rodada_id> <repeticao>
  ```

## Observações
- Os scripts PowerShell automatizam toda a execução, inclusive deploy no Kubernetes e análise dos resultados.
- Os resultados são salvos em CSV e podem ser analisados posteriormente.
- O projeto é multiplataforma, mas os scripts principais são para Windows (PowerShell).
- Para rodar em Linux, adapte os scripts ou use os Dockerfiles.
