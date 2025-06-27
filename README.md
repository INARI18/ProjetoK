# ProjetoK - Sistema Cliente-Servidor com Análise de Performance

Sistema completo de testes de carga cliente-servidor com protocolo PING/PONG, utiliza as linguagens Python e Go, e possui análise detalhada de performance e execução em ambientes locais, Docker e Kubernetes.

## 🚀 Execução Rápida

### Windows
```batch
scripts\executar_windows.bat
```

### Linux/macOS
```bash
chmod +x scripts/executar_linux.sh
./scripts/executar_linux.sh
```

## 📁 Estrutura do Projeto

```
ProjetoK/
├── src/                        # Código fonte
│   ├── cliente/               # Clientes Python e Go
│   ├── servidor/              # Servidor Python
│   └── testes/                # Scripts de teste e análise
├── resultados/                # Outputs organizados
│   ├── csv/                   # Dados em CSV
│   ├── graficos/              # Gráficos PNG
│   └── relatorios/            # Relatórios consolidados
├── config/                    # Configurações
│   ├── docker/                # Dockerfile
│   └── kubernetes/            # Manifests K8s
├── scripts/                   # Scripts de execução
├── docs/                      # Documentação completa
└── requirements.txt           # Dependências Python
```

## 📊 Recursos Implementados

- ✅ **Protocolo PING/PONG** sobre TCP/JSON
- ✅ **Múltiplas Linguagens**: Python e Go
- ✅ **Análise**: 10+ gráficos individuais por cenário
- ✅ **3000 Execuções**: 300 configurações × 10 repetições
- ✅ **Execução Flexível**: Local, Docker, Kubernetes
- ✅ **Scripts**: Windows e Linux
- ✅ **Estatísticas**: Máximo, mínimo, média, mediana, desvio padrão
- ✅ **Detecção de Outliers**: Z-score para limpeza de dados

## 📈 Cenários de Teste

- **Servidores**: 2, 4, 6, 8, 10 instâncias
- **Clientes**: 10 a 100 (incrementos de 10)
- **Mensagens por cliente**: 1, 10, 100, 500, 1000, 10000
- **Total**: 5 × 10 × 6 × 10 = **3000 execuções**

## 📊 Gráficos Gerados

### Gráficos Individuais por Cenário
- `analise_performance_1_mensagens.png`
- `analise_performance_10_mensagens.png`
- `analise_performance_100_mensagens.png`
- `analise_performance_500_mensagens.png`
- `analise_performance_1000_mensagens.png`
- `analise_performance_10000_mensagens.png`

### Gráfico Consolidado
- `analise_performance.png` (4 visualizações em 1)

## 📖 Documentação Completa

Para informações detalhadas sobre arquitetura, configuração e uso:

## 🔧 Requisitos Mínimos

- **Python 3.11+** com pip
- **Go 1.21+** 
- **Docker** (para containers)
- **Kubernetes** (para testes distribuídos)

## 📈 Resultados

Os testes geram automaticamente:
- Dados brutos em CSV
- Gráficos de análise visual
- Relatórios
- Comparações entre linguagens
- Métricas de escalabilidade
- Estatísticas com detecção de outliers

✅ **Atributos Implementados:**
- Protocolo definido e implementado (PING/PONG)
- Parâmetro configurável de mensagens
- Threading no servidor (1 thread por cliente)
- Registro detalhado em CSV
- Geração de gráficos comparativos
- Duas linguagens (Python + Go)
- Script de execução automatizada
- 3000 execuções conforme especificação
- Estatísticas avançadas (máx, mín, média, mediana, desvio padrão)
- Técnicas estatísticas (z-score) para remoção de outliers

---

**Desenvolvido para análise acadêmica de performance cliente-servidor distribuído.**
