# Scripts de Execução - ProjetoK

Scripts otimizados para execução automática dos testes em diferentes sistemas operacionais.

## Scripts Disponíveis

- **`executar_windows.bat`** - Script para Windows (PowerShell/CMD)
- **`executar_linux.sh`** - Script para Linux/macOS (Bash)

## Recursos dos Scripts

### Funcionalidades Comuns
- ✅ Detecção automática de ambiente
- ✅ Instalação de dependências
- ✅ Compilação do cliente Go
- ✅ Execução dos testes locais
- ✅ Geração de relatórios
- ✅ Limpeza de processos

### Funcionalidades Avançadas
- 🔄 Verificação de pré-requisitos
- 📊 Menu interativo de opções
- 🐳 Suporte a Docker (opcional)
- ☸️ Suporte a Kubernetes (opcional)
- 📝 Logs detalhados
- 🎨 Output colorido

## Execução

### Windows
```batch
scripts\executar_windows.bat
```

### Linux/macOS
```bash
chmod +x scripts/executar_linux.sh
./scripts/executar_linux.sh
```

## Personalização

Os scripts podem ser editados para:
- Alterar parâmetros de teste
- Adicionar/remover cenários
- Modificar configurações de Docker/K8s
- Personalizar outputs
