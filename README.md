# ProjetoK - Análise de Performance TCP

Projeto para análise de performance de comunicação TCP entre clientes e servidores usando **Go** e **Python**, com servidores executando em **Kubernetes** usando **imagens Docker customizadas**.

**TUDO é configurado automaticamente:**
- ✅ Verifica Docker e Python
- ✅ Baixa e instala Kubernetes (kind) se necessário
- ✅ Cria cluster com NodePort otimizado
- ✅ Baixa as imagens do Docker Hub
- ✅ Implanta servidores e executa testes

## 🐳 Imagens Docker

Este projeto usa imagens customizadas:

- **Servidor Go**: `bia18/projetok-servidor-go:latest` 
- **Servidor Python**: `bia18/projetok-servidor-python:latest`

### ⚠️ **ATENÇÃO: Uso de Recursos**

Este projeto realiza testes intensivos que utilizam recursos significativos:

#### **Recursos Utilizados:**
- **CPU**: Até **30 cores virtuais** no total (10 pods × 3 cores cada)
- **RAM**: Até **15GB** no pico (10 pods × 1.5GB cada)
- **Rede**: Tráfego TCP intenso entre clientes e servidores
- **Duração**: Aproximadamente 48-50 horas para testes completos

#### **Ambiente Testado:**
- **Processador**: Ryzen 5 5600GT (6 cores/12 threads) ✅
- **Memória**: 32GB DDR4 ✅

#### **⚙️ Para Hardware Mais Limitado:**
Se você tem menos recursos, pode editar os deployments em:
- `config/kubernetes/deployment-servidor-go.yaml`
- `config/kubernetes/deployment-servidor-python.yaml`

Reduza os valores de `requests` e `limits` para adequar ao seu hardware.

## 🛠️ Pré-Requisitos

- **Docker Desktop** (https://www.docker.com/products/docker-desktop)
- **Python 3.8+** com: `pip install matplotlib pandas seaborn`

## ⚡ Scripts Essenciais

1. **`teste_completo.bat`** - Executa TODOS os testes e gera gráficos em uma única etapa
2. **`scripts\executar_testes_go.bat`** - Configura ambiente e executa apenas testes Go
3. **`scripts\executar_testes_python.bat`** - Configura ambiente e executa apenas testes Python
4. **`scripts\gerar_graficos.bat`** - Gera gráficos comparativos

## 🌐 Arquitetura

### Servidores (Kubernetes)
- Deploy automático em pods Kubernetes
- **Acesso direto via NodePort**:
  - **Servidor Go**: `http://localhost:30001`
  - **Servidor Python**: `http://localhost:30002`
- Escalabilidade automática conforme configuração
- **Usa SUAS imagens customizadas**: Baixadas automaticamente do SEU Docker Hub (bia18)

### Clientes (Local)
- Executáveis locais que conectam diretamente aos NodePorts
- Go: `cliente_go.exe`, Python: `cliente.py`
- **Conectividade otimizada** para testes de performance

## 📊 Configurações de Teste

- **Servidores**: 2, 4, 6, 8, 10 replicas
- **Clientes**: 10-100 clientes simultâneos  
- **Mensagens**: 1-10000 mensagens por cliente
- **Repetições**: 10 execuções por configuração
- **Total**: 3.000 execuções por linguagem

## 🎯 Acesso aos Serviços

Após executar qualquer script de teste, os serviços estarão disponíveis em:

- **🔹 Servidor Go**: http://localhost:30001
  - Health check: http://localhost:30001/health
  - Endpoint principal: http://localhost:30001

- **🔹 Servidor Python**: http://localhost:30002  
  - Health check: http://localhost:30002/health
  - Endpoint principal: http://localhost:30002

## 📈 Resultados

- **JSON**: `resultados/relatorios/resultados_*_k8s_*.json`
- **Arquivos Parciais**: `resultados/relatorios/resultados_*_parciais.json`
- **Gráficos**: `resultados/graficos/*.png`
- **Relatório Estatístico**: `resultados/relatorios/relatorio_estatistico.csv`
- **Relatório Resumo**: `resultados/relatorios/relatorio_resumo.txt`

## 🔄 Fluxo de Desenvolvimento/Debug

### 1. Testar mudanças no código
```bash
# Atualizar suas imagens Docker
scripts\atualizar_imagens.bat
```

### 2. Executar testes
```bash
# Executar todos os testes de uma vez
teste_completo.bat

# OU executar testes específicos
# Testar apenas Go
scripts\executar_testes_go.bat

# Testar apenas Python  
scripts\executar_testes_python.bat
```

### 3. Analisar resultados
```bash
# Gerar gráficos comparativos
scripts\gerar_graficos.bat

# Localização dos resultados
resultados\graficos\relatorio_final_completo.png  # Gráfico principal
resultados\relatorios\relatorio_resumo.txt        # Resumo textual
```