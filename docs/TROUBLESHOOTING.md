# Guia de Solução de Problemas - ProjetoK

## Problema Identificado
O script foi executado do diretório errado (C:\ em vez de C:\Users\Bia\Desktop\ProjetoK\), causando erros de "arquivo não encontrado".

## ✅ Soluções Disponíveis

### Opção 1: Script PowerShell Corrigido (Recomendado)
```powershell
# Navegar para o diretório do projeto
cd "C:\Users\Bia\Desktop\ProjetoK"

# Executar apenas testes locais (sem Kubernetes)
.\executar_testes.ps1 -LocalOnly

# OU executar tudo (se Kubernetes estiver configurado)
.\executar_testes.ps1
```

### Opção 2: Script Local Simples
```powershell
# Navegar para o diretório do projeto
cd "C:\Users\Bia\Desktop\ProjetoK"

# Executar script local simplificado
.\executar_local.ps1

# OU com compilação Go
.\executar_local.ps1 -CompileGo
```

### Opção 3: Script Batch (Mais Simples)
```cmd
cd "C:\Users\Bia\Desktop\ProjetoK"
executar_local.bat
```

### Opção 4: Execução Manual
```powershell
cd "C:\Users\Bia\Desktop\ProjetoK"

# Instalar dependências
pip install -r requirements.txt

# Compilar Go (opcional)
cd files
go build -o cliente.exe cliente.go
cd ..

# Executar testes
cd files
python teste_carga.py
cd ..
```

## 🔧 Verificações Importantes

### 1. Diretório Correto
Certifique-se de estar em: `C:\Users\Bia\Desktop\ProjetoK\`

### 2. Estrutura do Projeto
Verifique se existem:
- `files\teste_carga.py`
- `files\servidor.py` 
- `files\cliente.py`
- `requirements.txt`

### 3. Dependências
- **Python 3.10+**: `python --version`
- **Pip**: `pip --version`
- **Go (opcional)**: `go version`

## 🐳 Problemas Kubernetes/Docker

### Cluster Kubernetes Não Disponível
- Use `-LocalOnly` para pular testes Kubernetes
- Instale Docker Desktop ou configure kubectl

### Docker Build Falhou
- Use `-SkipDocker` para usar imagem existente
- Verifique se Docker está rodando

### Imagem Push Falhou
- Não é crítico para testes locais
- Configure credenciais Docker Hub se necessário

## 📊 Resultados Esperados

Após execução bem-sucedida, você deve ter:
- `files\resultados_teste_carga.csv`: Dados dos testes
- `files\analise_performance.png`: Gráficos
- `files\relatorio_detalhado.csv`: Estatísticas
- `files\comparacao_linguagens.csv`: Python vs Go

## 🚨 Comandos de Emergência

### Se Tudo Falhou - Teste Mínimo
```powershell
cd "C:\Users\Bia\Desktop\ProjetoK\files"
python -c "
import subprocess
import time

# Teste básico servidor-cliente
print('Iniciando servidor...')
servidor = subprocess.Popen(['python', 'servidor.py', '--porta', '8000'])
time.sleep(2)

print('Testando cliente...')
subprocess.run(['python', 'cliente.py', '--host', '127.0.0.1', '--porta', '8000', '--mensagens', '1'])

servidor.terminate()
print('Teste básico concluído!')
"
```

## 📋 Checklist de Validação

- [ ] Diretório correto (`ProjetoK\`)
- [ ] Python funcionando
- [ ] Dependências instaladas
- [ ] Arquivos do projeto existem
- [ ] Testes executam sem erro
- [ ] Resultados são gerados

## 💡 Dicas de Performance

### Para Testes Rápidos
Edite `files\teste_carga.py` e reduza os loops:
```python
# Teste rápido: apenas 2 configurações
for servidores in range(2, 5, 2):        # 2, 4
    for clientes in range(10, 31, 10):   # 10, 20, 30
        for mensagens in [1, 10]:        # 1, 10
```

### Para Debug
Adicione prints no código:
```python
print(f"Testando: {servidores} servidores, {clientes} clientes, {mensagens} mensagens")
```

## 🔍 Logs de Erro Comuns

### "Path does not exist"
- **Causa**: Diretório errado
- **Solução**: `cd` para o diretório correto

### "Python not found"
- **Causa**: Python não instalado ou não no PATH
- **Solução**: Instalar Python 3.10+

### "Permission denied"
- **Causa**: PowerShell executado sem privilégios
- **Solução**: "Executar como Administrador"

### "Module not found"
- **Causa**: Dependências não instaladas
- **Solução**: `pip install -r requirements.txt`
