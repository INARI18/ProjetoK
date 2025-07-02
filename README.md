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

## � Requisitos de Hardware

### ⚠️ **ATENÇÃO: Uso de Recursos**

Este projeto pode usar recursos significativos:

#### **Configuração Dos Testes:**
- **RAM**: Até **10GB** com configuração máxima (10 pods × 1GB cada)
- **CPU**: Até **20 cores** virtuais (10 pods × 2 cores cada)  
- **Rede**: Tráfego intenso TCP entre clientes e servidores     

#### **Configuração Testada (Ideal):**
- **CPU**: Ryzen 5 5600GT (6 cores/12 threads) ✅
- **RAM**: 32GB ✅  
- **Resultado**: Performance excelente com todos os recursos

#### **⚙️ Para Hardware Mais Limitado:**
Se você tem menos recursos, pode editar os deployments em:
- `config/kubernetes/deployment-servidor-go.yaml`
- `config/kubernetes/deployment-servidor-python.yaml`

Reduza os valores de `requests` e `limits` para adequar ao seu hardware.

## �🛠️ Pré-requisitos

- **Docker Desktop** (https://www.docker.com/products/docker-desktop)
- **Python 3.8+** com: `pip install matplotlib pandas seaborn`

## ⚡ Scripts Essenciais

1. **`teste_completo.bat`** - Executa TODOS os testes e gera gráficos em uma única etapa
2. **`scripts\executar_testes_go.bat`** - Configura ambiente e executa apenas testes Go
3. **`scripts\executar_testes_python.bat`** - Configura ambiente e executa apenas testes Python
4. **`scripts\gerar_graficos.bat`** - Gera gráficos comparativos
5. **`scripts\atualizar_imagens.bat`** - Atualiza suas imagens no Docker Hub (dev only)

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

## 🔧 Comandos Úteis

```bash
# Status Kubernetes
kubectl get pods
kubectl get services

# Monitorar recursos (CPU/RAM)
kubectl top pods
kubectl top nodes

# Logs
kubectl logs [nome-do-pod]

# Escalar serviços (ajustar conforme seu hardware)
kubectl scale deployment servidor-go-deployment --replicas=5
kubectl scale deployment servidor-python-deployment --replicas=3

# Limpar ambiente (opcional)
scripts\limpar_ambiente.bat
```

## 🆘 Solução de Problemas

### Problema: "Docker não encontrado"
**Solução**: Instale Docker Desktop: https://www.docker.com/products/docker-desktop

### Problema: "Erro ao criar cluster"  
**Solução**: 
1. Verifique se Docker Desktop está rodando
2. Execute: `scripts\limpar_ambiente.bat`
3. Execute novamente o script de teste

### Problema: "Pods não ficam prontos"
**Solução**:
1. Verifique conectividade com internet (para baixar imagens)
2. Execute: `kubectl get pods` para ver status
3. Execute: `kubectl logs [nome-do-pod]` para ver erros

### Problema: "Sistema lento/travando durante testes"
**Solução**:
1. **Monitor recursos**: Execute `kubectl top pods` e `kubectl top nodes`
2. **Hardware limitado**: Edite os deployments em `config/kubernetes/` e reduza:
   - `resources.requests.memory` (ex: de "768Mi" para "384Mi")
   - `resources.requests.cpu` (ex: de "1500m" para "750m") 
   - `resources.limits.memory` (ex: de "1.5Gi" para "768Mi")
   - `resources.limits.cpu` (ex: de "3000m" para "1500m")
3. **Escale menos pods**: Reduza configurações de servidores para [2, 4, 6] em vez de [2, 4, 6, 8, 10]

### Problema: "Out of memory" ou "Docker Desktop travando"
**Solução**:
1. **Aumente RAM do Docker Desktop**: Settings → Resources → Memory (min 8GB)
2. **Reduza configuração**: Edite `deployment-servidor-*.yaml` (reduza limits)
3. **Execute por partes**: Teste Go primeiro, depois Python separadamente

### Problema: "Resultados inconsistentes"
**Solução**:
1. Execute: `scripts\atualizar_imagens.bat` (se mudou código)
2. Execute: `scripts\limpar_ambiente.bat` (limpar cache)
3. Execute novamente os testes