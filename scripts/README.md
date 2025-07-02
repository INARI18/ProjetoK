# Scripts - ProjetoK

Scripts essenciais para execução completa dos testes e análises.

## 📋 Scripts Disponíveis (apenas 4)

### 🚀 **Execução de Testes**
- **`executar_testes_go.bat`** - Executa testes completos com servidores Go
- **`executar_testes_python.bat`** - Executa testes completos com servidores Python
- **`gerar_graficos.bat`** - Gera gráficos comparativos dos resultados

### � **Manutenção (apenas para você)**
- **`atualizar_imagens.bat`** - Atualiza as imagens Docker Hub (quando modificar código)

## 🎯 Fluxo Simplificado

### Para Executar Testes (usuários normais):
```bash
# Executar testes Go
scripts\executar_testes_go.bat

# Executar testes Python  
scripts\executar_testes_python.bat

# Gerar gráficos comparativos
scripts\gerar_graficos.bat
```

### Para Atualizar Imagens (apenas você):
```bash
# Quando modificar código dos servidores
scripts\atualizar_imagens.bat
```

## 💡 Observações Importantes

- **Imagens Docker**: São baixadas automaticamente do Docker Hub
- **Sem login necessário**: Para executar testes (imagens são públicas)
- **Login só para atualizar**: Apenas você precisa fazer login para atualizar imagens
- **Execução independente**: Cada teste (Go/Python) roda separadamente

## 📊 Resultados

Todos os scripts geram resultados em:
- **JSON**: `resultados/resultados_*_k8s_*.json`
- **Gráficos**: `resultados/graficos/`
- **Relatórios**: `resultados/relatorios/`

## 🛠️ Requisitos

- Docker Desktop com Kubernetes habilitado
- Python 3.8+ com matplotlib, pandas, seaborn
- Go 1.21+ (para compilar clientes)
- kubectl configurado
- Conta Docker Hub (apenas para build/push)

## ⚡ Execução Rápida

```bash
# Validar ambiente
python validar_projeto.py

# Baixar imagens (primeira vez)
scripts\pull-imagens-dockerhub.bat

# Executar testes completos
scripts\executar_testes_go.bat
scripts\executar_testes_python.bat

# Gerar análises visuais
scripts\gerar_graficos.bat
```