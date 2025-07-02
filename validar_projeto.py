#!/usr/bin/env python3
"""
Script de validação do ProjetoK
Verifica se toda a estrutura está correta e funcionando
"""

import os
import sys
import subprocess
from pathlib import Path

def log_info(msg):
    print(f"[INFO] {msg}")

def log_success(msg):
    print(f"[✓] {msg}")

def log_error(msg):
    print(f"[✗] {msg}")

def verificar_imagens_docker():
    """Verifica se as imagens Docker estão disponíveis no Docker Hub"""
    log_info("Verificando disponibilidade das imagens Docker no Docker Hub...")
    
    try:
        # Verificar se Docker está disponível
        result = subprocess.run(["docker", "--version"], capture_output=True, text=True, timeout=10)
        if result.returncode != 0:
            log_error("Docker não está disponível")
            return False
        
        log_success("Docker encontrado")
        
        # Verificar se consegue fazer pull da imagem Go
        log_info("Verificando imagem Go no Docker Hub...")
        result = subprocess.run(["docker", "manifest", "inspect", "bia18/projetok-servidor-go:latest"], 
                              capture_output=True, text=True, timeout=30)
        if result.returncode == 0:
            log_success("Imagem Go disponível no Docker Hub: bia18/projetok-servidor-go:latest")
        else:
            log_error("Imagem Go não encontrada no Docker Hub: bia18/projetok-servidor-go:latest")
            log_info("Execute: scripts\\build-push-dockerhub.bat")
            return False
        
        # Verificar se consegue fazer pull da imagem Python
        log_info("Verificando imagem Python no Docker Hub...")
        result = subprocess.run(["docker", "manifest", "inspect", "bia18/projetok-servidor-python:latest"], 
                              capture_output=True, text=True, timeout=30)
        if result.returncode == 0:
            log_success("Imagem Python disponível no Docker Hub: bia18/projetok-servidor-python:latest")
        else:
            log_error("Imagem Python não encontrada no Docker Hub: bia18/projetok-servidor-python:latest")
            log_info("Execute: scripts\\build-push-dockerhub.bat")
            return False
            
        return True
        
    except FileNotFoundError:
        log_error("Docker não está instalado")
        log_info("Instale Docker Desktop para usar imagens customizadas")
        return False
    except subprocess.TimeoutExpired:
        log_error("Timeout ao verificar Docker Hub")
        return False

def verificar_arquivos_executaveis():
    """Verifica se os executáveis Go estão presentes ou se podem ser compilados"""
    log_info("Verificando executáveis Go...")
    
    # Verificar se cliente Go está compilado  
    cliente_go_exe = "src/cliente (local)/cliente_go.exe"
    if os.path.exists(cliente_go_exe):
        log_success("Cliente Go compilado encontrado")
    else:
        log_info("Cliente Go não compilado (será compilado automaticamente se necessário)")
    
    return True

def verificar_estrutura():
    """Verifica se todos os arquivos necessários existem"""
    log_info("Verificando estrutura do projeto...")
    
    arquivos_necessarios = [
        # Clientes (executam localmente)
        "src/cliente (local)/cliente.py", 
        "src/cliente (local)/cliente.go",
        "src/cliente (local)/go.mod",
        
        # Scripts de teste (em src/testes)
        "src/testes/teste_carga.py",
        "src/testes/graficos.py",
        "src/testes/executar_testes_python.py",
        "src/testes/executar_testes_go.py",
        
        # Configurações Kubernetes
        "config/kubernetes/deployment-servidor-go.yaml",
        "config/kubernetes/deployment-servidor-python.yaml",
        "config/kubernetes/service-servidor.yaml",
        
        # Scripts de execução (apenas 3 essenciais)
        "scripts/executar_testes_python.bat",
        "scripts/executar_testes_go.bat",
        "scripts/gerar_graficos.bat",
        
        # Arquivos de configuração
        "requirements.txt",
        "README.md"
    ]
    
    todos_ok = True
    for arquivo in arquivos_necessarios:
        if os.path.exists(arquivo):
            log_success(f"Arquivo encontrado: {arquivo}")
        else:
            log_error(f"Arquivo AUSENTE: {arquivo}")
            todos_ok = False
    
    return todos_ok

def verificar_pastas_resultados():
    """Verifica se as pastas de resultados existem"""
    log_info("Verificando pastas de resultados...")
    
    pastas = [
        "resultados",
        "resultados/graficos"
    ]
    
    for pasta in pastas:
        if os.path.exists(pasta):
            log_success(f"Pasta encontrada: {pasta}")
        else:
            log_error(f"Pasta AUSENTE: {pasta}")
            try:
                os.makedirs(pasta, exist_ok=True)
                log_success(f"Pasta criada: {pasta}")
            except Exception as e:
                log_error(f"Erro ao criar pasta {pasta}: {e}")
                return False
    
    return True

def verificar_dependencias():
    """Verifica se as dependências Python estão instaladas"""
    log_info("Verificando dependências Python...")
    
    try:
        import matplotlib
        log_success("matplotlib instalado")
    except ImportError:
        log_error("matplotlib NÃO instalado")
        return False
    
    try:
        import pandas  
        log_success("pandas instalado")
    except ImportError:
        log_error("pandas NÃO instalado")
        return False
    
    try:
        import seaborn
        log_success("seaborn instalado")
    except ImportError:
        log_error("seaborn NÃO instalado")
        return False
    
    return True

def verificar_go():
    """Verifica se Go está disponível e se os programas compilam"""
    log_info("Verificando Go...")
    
    # Lista de possíveis localizações do Go
    go_paths = [
        "go",  # Se estiver no PATH
        r"C:\Program Files\Go\bin\go.exe",  # Local padrão Windows
        r"C:\Go\bin\go.exe",  # Local alternativo Windows
        "/usr/local/go/bin/go",  # Local padrão Linux/macOS
        "/usr/bin/go",  # Local alternativo Linux
    ]
    
    go_encontrado = False
    for go_path in go_paths:
        try:
            if os.path.exists(go_path) or go_path == "go":
                result = subprocess.run([go_path, "version"], capture_output=True, text=True)
                if result.returncode == 0:
                    log_success(f"Go encontrado em: {go_path}")
                    log_success(f"Versão: {result.stdout.strip()}")
                    go_encontrado = True
                    break
        except (FileNotFoundError, subprocess.SubprocessError):
            continue
    
    if not go_encontrado:
        log_error("Go não encontrado nos locais comuns")
        log_info("Locais verificados:")
        for path in go_paths:
            log_info(f"  - {path}")
        return False
    
    # Verificar se cliente Go já está compilado
    cliente_go_exe = "src/cliente (local)/cliente_go.exe"
    if os.path.exists(cliente_go_exe):
        log_success("Cliente Go já compilado encontrado")
    else:
        log_info("Cliente Go não compilado, tentando compilar...")
        try:
            result = subprocess.run(
                ["go", "build", "-o", "cliente_go.exe", "cliente.go"],
                capture_output=True, text=True, cwd="src/cliente (local)"
            )
            if result.returncode == 0:
                log_success("Cliente Go compilado com sucesso")
            else:
                log_error(f"Erro ao compilar cliente Go: {result.stderr}")
                return False
        except Exception as e:
            log_error(f"Erro ao compilar cliente Go: {e}")
            return False
    
    return True

def verificar_kubernetes():
    """Verifica se kubectl está disponível e funcionando"""
    log_info("Verificando Kubernetes (kubectl)...")
    
    try:
        result = subprocess.run(["kubectl", "version", "--client"], 
                              capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            log_success("kubectl encontrado e funcionando")
            
            # Verificar se cluster está acessível
            try:
                result = subprocess.run(["kubectl", "cluster-info"], 
                                      capture_output=True, text=True, timeout=10)
                if result.returncode == 0:
                    log_success("Cluster Kubernetes acessível")
                    return True
                else:
                    log_error("Cluster Kubernetes não acessível")
                    log_info("Execute 'kubectl cluster-info' para diagnosticar")
                    return False
            except subprocess.TimeoutExpired:
                log_error("Timeout ao verificar cluster Kubernetes")
                return False
                
        else:
            log_error("kubectl não está funcionando corretamente")
            return False
            
    except FileNotFoundError:
        log_error("kubectl não encontrado")
        log_info("Instale kubectl para usar os servidores Kubernetes")
        return False
    except subprocess.TimeoutExpired:
        log_error("Timeout ao verificar kubectl")
        return False

def teste_importacao():
    """Testa se os módulos podem ser importados"""
    log_info("Testando importações...")
    
    # Adicionar src ao path
    sys.path.insert(0, 'src')
    
    try:
        from testes import graficos
        log_success("graficos.py importado com sucesso")
    except ImportError as e:
        log_error(f"Erro ao importar graficos: {e}")
        return False
    
    return True

def main():
    print("=" * 60)
    print("VALIDAÇÃO DO PROJETOK - ESTRUTURA KUBERNETES")
    print("=" * 60)
    print(f"📁 Projeto: ProjetoK")
    print(f"🏗️  Arquitetura: Servidores Kubernetes + Clientes Locais")
    print(f"🌐 Linguagens: Python + Go")
    print("=" * 60)
    
    # Verificar se estamos no diretório correto
    if not os.path.exists("src/testes/teste_carga.py"):
        log_error("Execute este script do diretório raiz do ProjetoK!")
        return False
    
    # Executar verificações básicas
    checks_basicos = [
        verificar_estrutura(),
        verificar_pastas_resultados(),
        verificar_dependencias(),
        verificar_arquivos_executaveis(),
        teste_importacao()
    ]
    
    # Verificações opcionais
    go_ok = verificar_go()
    kubernetes_ok = verificar_kubernetes()
    docker_ok = verificar_imagens_docker()
    
    # Resultado final
    print("\n" + "=" * 60)
    print("RESULTADO DA VALIDAÇÃO")
    print("=" * 60)
    
    if all(checks_basicos):
        log_success("ESTRUTURA BÁSICA OK! Arquivos e dependências Python corretos.")
        
        print(f"\n📋 RESUMO DO AMBIENTE:")
        print(f"  ✅ Estrutura de arquivos: OK")
        print(f"  ✅ Dependências Python: OK")
        print(f"  {'✅' if go_ok else '❌'} Go disponível: {'SIM' if go_ok else 'NÃO'}")
        print(f"  {'✅' if kubernetes_ok else '❌'} Kubernetes: {'ACESSÍVEL' if kubernetes_ok else 'INDISPONÍVEL'}")
        print(f"  {'✅' if docker_ok else '❌'} Imagens Docker: {'CRIADAS' if docker_ok else 'FALTANDO'}")
        
        print(f"\n🚀 OPÇÕES DE EXECUÇÃO DISPONÍVEIS:")
        
        if kubernetes_ok and go_ok and docker_ok:
            print("1. ✅ Testes Go (Kubernetes): scripts\\executar_testes_go.bat")
            print("2. ✅ Testes Python (Kubernetes): scripts\\executar_testes_python.bat")
            print("3. ✅ Gerar Gráficos: scripts\\gerar_graficos.bat")
            print("\n🎉 CONFIGURAÇÃO COMPLETA! Todos os testes disponíveis.")
            
        elif not docker_ok:
            print("1. ❌ Testes Go: INDISPONÍVEL (Imagens Docker necessárias)")
            print("2. ❌ Testes Python: INDISPONÍVEL (Imagens Docker necessárias)")
            print("3. ✅ Gerar Gráficos: scripts\\gerar_graficos.bat (se houver dados)")
            print("\n⚠️  Execute scripts\\build-imagens.bat para criar as imagens")
            
        elif not kubernetes_ok:
            print("1. ❌ Testes Go: INDISPONÍVEL (Kubernetes não acessível)")
            print("2. ❌ Testes Python: INDISPONÍVEL (Kubernetes não acessível)")
            print("3. ✅ Gerar Gráficos: scripts\\gerar_graficos.bat (se houver dados)")
            print("\n⚠️  Configure Kubernetes para executar testes")
            
        elif not go_ok:
            print("1. ❌ Testes Go: INDISPONÍVEL (Go não encontrado)")
            print("2. ✅ Testes Python (Kubernetes): scripts\\executar_testes_python.bat")
            print("3. ✅ Gerar Gráficos: scripts\\gerar_graficos.bat")
            print("\n⚠️  Instale Go para habilitar testes Go")
            
        else:
            print("1. ❌ Testes: INDISPONÍVEL (Múltiplas dependências faltando)")
            print("2. ✅ Gerar Gráficos: scripts\\gerar_graficos.bat (se houver dados)")
            print("\n⚠️  Verifique as dependências acima")
        
        print(f"\n📊 RESULTADOS SERÃO SALVOS EM:")
        print(f"  - JSON: resultados/resultados_*_k8s_*.json")
        print(f"  - CSV: resultados/relatorio_estatistico.csv")
        print(f"  - TXT: resultados/resumo_executivo.txt")
        print(f"  - PNG: resultados/graficos/*.png")
        
        print(f"\n🔧 COMANDOS ÚTEIS:")
        print(f"  - Listar pods: kubectl get pods")
        print(f"  - Logs do servidor: kubectl logs <pod-name>")
        print(f"  - Aplicar configs: kubectl apply -f config/kubernetes/")
        print(f"  - Deletar recursos: kubectl delete -f config/kubernetes/")
            
    else:
        log_error("VALIDAÇÃO FALHOU! Corrija os problemas de estrutura acima.")
        return False
    
    print("=" * 60)
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
