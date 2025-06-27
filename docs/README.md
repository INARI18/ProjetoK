# ProjetoK - Sistema Cliente-Servidor com Análise de Performance

Este projeto implementa um sistema cliente-servidor distribuído com análise de performance, utilizando Python e Go como linguagens de programação e Kubernetes para orquestração.

## 📋 Características Implementadas

### 1. Protocolo de Comunicação
- **Formato**: JSON sobre TCP
- **Estrutura da Mensagem**:
  ```json
  {
    "type": "request",
    "client_id": "cliente_12345",
    "timestamp": 1703001234567,
    "sequence": 1,
    "data": "Mensagem 1 do cliente cliente_12345"
  }
  ```
- **Protocolo de Tamanho**: Cada mensagem é precedida por 8 bytes indicando o tamanho

### 2. Múltiplas Linguagens
- **Cliente Python**: `src/cliente/cliente.py`
- **Cliente Go**: `src/cliente/cliente.go`
- **Servidor Python**: `src/servidor/servidor.py` (com suporte a threads)

### 3. Cenários de Teste
- **Servidores**: 2, 4, 6, 8, 10 instâncias
- **Clientes**: 10 a 100 (incrementos de 10)
- **Mensagens por cliente**: 1, 10, 100
- **Total**: 150 cenários de teste (5 × 10 × 3)

### 4. Registro e Análise
- **CSV de requisições**: Registro detalhado por servidor
- **CSV de resultados**: Análise consolidada de performance
- **Gráficos**: 9 visualizações diferentes de performance

## 🚀 Como Executar

### Execução Automatizada (Recomendado)

#### Windows (PowerShell):
```powershell
# Execução completa (local + Kubernetes)
.\scripts\executar_windows.bat

# Para opções específicas, edite o script conforme necessário
```

#### Linux/macOS (Bash):
```bash
# Dar permissão de execução
chmod +x scripts/executar_linux.sh

# Execução completa
./scripts/executar_linux.sh
```

### Execução Manual

#### 1. Preparar Ambiente
```bash
# Instalar dependências Python
pip install -r requirements.txt

# Compilar cliente Go (opcional)
cd src/cliente
go build -o cliente cliente.go
cd ../..
```

#### 2. Teste Local
```bash
cd src/testes
python teste_carga.py
```

#### 3. Kubernetes
```bash
# Construir imagem
docker build -f config/docker/Dockerfile -t bia18/projetok:latest .
docker push bia18/projetok:latest

# Deploy
kubectl apply -f config/kubernetes/
```

## 📊 Resultados e Análises

### Arquivos Gerados
- `resultados/csv/resultados_teste_carga.csv`: Dados brutos de todos os testes
- `resultados/graficos/analise_performance.png`: Gráficos de análise visual
- `resultados/relatorios/relatorio_detalhado.csv`: Estatísticas agregadas
- `resultados/csv/comparacao_linguagens.csv`: Comparação Python vs Go
- `resultados/csv/requests_porta_*.csv`: Logs detalhados por servidor

### Métricas Coletadas
- **Tempo de Resposta**: Latência média por configuração
- **Throughput**: Requisições por segundo
- **Taxa de Erro**: Percentual de falhas
- **Scalabilidade**: Performance vs número de servidores
- **Comparação de Linguagens**: Python vs Go

### Gráficos Disponíveis
1. Tempo Médio vs Clientes
2. Throughput vs Clientes  
3. Comparação Python vs Go
4. Heatmap de Tempo Médio
5. Heatmap de Throughput
6. Scalabilidade por Servidores
7. Taxa de Erro vs Carga
8. Distribuição de Tempos
9. Resumo Estatístico

## 🏗️ Arquitetura

### Estrutura do Projeto
```
ProjetoK/
├── src/
│   ├── servidor/
│   │   └── servidor.py          # Servidor Python com threads
│   ├── cliente/
│   │   ├── cliente.py           # Cliente Python
│   │   ├── cliente.go           # Cliente Go
│   │   └── go.mod              # Configuração Go
│   └── testes/
│       ├── teste_carga.py       # Orquestrador de testes
│       └── graficos.py          # Geração de relatórios
├── resultados/
│   ├── csv/                     # Dados em CSV
│   ├── graficos/               # Gráficos PNG
│   └── relatorios/             # Relatórios consolidados
├── config/
│   ├── docker/
│   │   └── Dockerfile          # Multi-stage build
│   └── kubernetes/
│       ├── deployment-servidor.yaml
│       ├── service-servidor.yaml
│       └── job-teste-carga.yaml
├── scripts/
│   ├── executar_windows.bat    # Script Windows
│   └── executar_linux.sh       # Script Linux/macOS
├── docs/
│   ├── README.md               # Este arquivo
│   └── TROUBLESHOOTING.md      # Guia de problemas
└── requirements.txt            # Dependências Python
```

### Protocolo de Comunicação
1. Cliente conecta ao servidor via TCP
2. Para cada mensagem:
   - Envia 8 bytes com tamanho da mensagem
   - Envia mensagem JSON
   - Recebe 8 bytes com tamanho da resposta
   - Recebe resposta JSON
3. Servidor registra cada requisição em CSV

### Threading no Servidor
- Uma thread por cliente conectado
- Thread-safe para escrita em CSV (usando locks)
- Suporte a múltiplas conexões simultâneas

## 📈 Análise de Performance

### Fatores Analisados
- **Escalabilidade Horizontal**: Como performance varia com número de servidores
- **Carga de Trabalho**: Impacto do número de clientes e mensagens
- **Linguagem**: Comparação Python vs Go
- **Latência vs Throughput**: Trade-offs de performance

### Cenários de Teste Específicos
- **Baixa Carga**: 10 clientes, 1 mensagem
- **Carga Média**: 50 clientes, 10 mensagens  
- **Alta Carga**: 100 clientes, 100 mensagens

## 🔧 Requisitos do Sistema

### Software Necessário
- **Python 3.10+** com pip
- **Go 1.21+** (opcional, para cliente Go)
- **Docker** (para containers)
- **Kubernetes** (kubectl configurado)

### Dependências Python
- matplotlib==3.10.3
- pandas==2.2.3
- seaborn==0.13.2

## 🐳 Docker e Kubernetes

### Imagem Docker
- **Base**: Multi-stage build (Go + Python)
- **Tamanho**: Otimizado com Alpine
- **Conteúdo**: Servidor Python + Cliente Go + Dependências

### Recursos Kubernetes
- **Deployment**: Servidores com recursos limitados
- **Service**: LoadBalancer interno para distribuição
- **Job**: Execução de testes de carga

## 📝 Logs e Monitoramento

### Tipos de Log
- **Servidor**: Registro de cada requisição processada
- **Cliente**: Métricas de tempo de resposta
- **Teste**: Consolidação de resultados por cenário

### Campos Registrados
- Timestamp de requisição e resposta
- ID do cliente e sequência da mensagem  
- Tempo de resposta em milissegundos
- Status da operação
- Porta do servidor

## 🔍 Troubleshooting

### Problemas Comuns
1. **Go não encontrado**: Instalar Go ou usar apenas Python
2. **Docker sem permissão**: Configurar usuário no grupo docker
3. **Kubernetes não conectado**: Verificar kubectl config
4. **Porta ocupada**: Ajustar PORTA_BASE no teste_carga.py

### Debug
```bash
# Ver logs do servidor
kubectl logs deployment/servidor-deployment

# Ver status dos jobs
kubectl get jobs

# Logs detalhados do teste
kubectl logs job/job-teste-carga

# Testar localmente
cd src/testes && python teste_carga.py
```

## 🤝 Contribuição

Este projeto atende aos requisitos acadêmicos especificados:
- ✅ Protocolo definido e implementado
- ✅ Parâmetro configurável de mensagens
- ✅ Threading no servidor
- ✅ Registro em CSV
- ✅ Geração de gráficos  
- ✅ Duas linguagens (Python + Go)
- ✅ Script de execução automatizada
- ✅ 150+ cenários de teste
