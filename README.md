## Descrição

ProjetoK é um ambiente de testes de desempenho para servidores TCP implementados em Go e Python, com clientes também nessas linguagens. O objetivo é comparar o desempenho dos servidores sob diferentes cargas, utilizando automação de testes, análise estatística e geração de relatórios. A nova versão do sistema explora ao máximo o paralelismo interno: clientes Go usam goroutines e clientes Python usam corrotinas (asyncio), permitindo comparar a escalabilidade real de cada linguagem em cenários altamente concorrentes.

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
   O script irá:
   - Criar/atualizar o cluster Kubernetes com kind
   - Fazer deploy dos servidores Go e Python
   - Rodar testes de carga com clientes Go e Python, usando paralelismo interno (goroutines/corrotinas)
   - Gerar arquivos CSV de resultados em `src/results/reports/`
   - Analisar os resultados e gerar relatórios estatísticos
   - Gerar gráficos comparativos automaticamente em `src/results/charts/`

4. **(Opcional) Rodar análise manual:**
   ```powershell
   python src/tools/analyze_results.py src/results/reports/test-go.csv go
   python src/tools/analyze_results.py src/results/reports/test-python.csv python
   python src/tools/generate_charts.py
   ```
   Os gráficos serão salvos em `src/results/charts/`.


## Sobre os gráficos

- Os gráficos gerados são 3D, com cada eixo representando throughput, número de clientes e número de servidores.
- Cada gráfico mostra Go e Python juntos, facilitando a comparação direta.
- Cada gráfico corresponde a um cenário de teste com uma quantidade fixa de mensagens por cliente (1, 10, 100, 500, 1000, 10000).
- Os arquivos dos gráficos são salvos em `src/results/charts/`.

## Observação importante sobre o client-go no WSL2

> **Atenção:** O binário `client-go` para uso no WSL2 (Linux) **não é criado automaticamente**. Para rodar os testes no WSL2, compile manualmente o binário Linux:
> ```powershell
> wsl -d Ubuntu -- go build -o /home/<usuario_wsl>/client-go /mnt/c/Users/Bia/Desktop/ProjetoK/src/client/client-go.go
> ```
> Substitua `<usuario_wsl>` pelo seu usuário do WSL2 **e ajuste o caminho `/mnt/c/Users/Bia/Desktop/ProjetoK/...` para o local onde você clonou o projeto no seu Windows**.


## Como rodar manualmente um cliente

- **Go:**
  ```powershell
  .\src\client\client-go.exe <host> <porta> <num_msgs> <num_clientes> <cliente_id> <num_servidores> <num_clientes_total> <cenario_id> <repeticao>
  ```
- **Python:**
  ```powershell
  python src/client/client-python.py <host> <porta> <num_msgs> <num_clientes> <cliente_id> <num_servidores> <num_clientes_total> <cenario_id> <repeticao>
  ```

## Observações
- Os scripts PowerShell automatizam toda a execução, incluindo deploy no Kubernetes, análise dos resultados e geração de gráficos.
- Os resultados são salvos em CSV e podem ser analisados posteriormente.
- O projeto é multiplataforma, mas os scripts principais são para Windows (PowerShell). Para rodar em Linux, adapte os scripts ou utilize os Dockerfiles.
- A nova versão explora o máximo de paralelismo possível em cada linguagem, evidenciando as diferenças reais de desempenho entre Go (goroutines) e Python (corrotinas/asyncio).