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

def verificar_estrutura():
    """Verifica se todos os arquivos necessários existem"""
    log_info("Verificando estrutura do projeto...")
    
    arquivos_necessarios = [
        "src/servidor/servidor.py",
        "src/cliente/cliente.py", 
        "src/cliente/cliente.go",
        "src/testes/teste_carga.py",
        "src/testes/graficos.py",
        "config/docker/Dockerfile",
        "config/kubernetes/deployment-servidor.yaml",
        "config/kubernetes/service-servidor.yaml", 
        "config/kubernetes/job-teste-carga.yaml",
        "scripts/executar_windows.bat",
        "scripts/executar_linux.sh",
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
        "resultados/csv", 
        "resultados/graficos",
        "resultados/relatorios"
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
    """Verifica se Go está disponível"""
    log_info("Verificando Go...")
    
    # Lista de possíveis localizações do Go
    go_paths = [
        "go",  # Se estiver no PATH
        r"C:\Program Files\Go\bin\go.exe",  # Local padrão Windows
        r"C:\Go\bin\go.exe",  # Local alternativo Windows
        "/usr/local/go/bin/go",  # Local padrão Linux/macOS
        "/usr/bin/go",  # Local alternativo Linux
    ]
    
    for go_path in go_paths:
        try:
            if os.path.exists(go_path) or go_path == "go":
                result = subprocess.run([go_path, "version"], capture_output=True, text=True)
                if result.returncode == 0:
                    log_success(f"Go encontrado em: {go_path}")
                    log_success(f"Versão: {result.stdout.strip()}")
                    return True
        except (FileNotFoundError, subprocess.SubprocessError):
            continue
    
    log_error("Go não encontrado nos locais comuns")
    log_info("Locais verificados:")
    for path in go_paths:
        log_info(f"  - {path}")
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
    print("VALIDAÇÃO DO PROJETOK")
    print("=" * 60)
    
    # Verificar se estamos no diretório correto
    if not os.path.exists("src/testes/teste_carga.py"):
        log_error("Execute este script do diretório raiz do ProjetoK!")
        return False
    
    # Executar verificações
    checks = [
        verificar_estrutura(),
        verificar_pastas_resultados(),
        verificar_dependencias(),
        teste_importacao()
    ]
    
    # Verificação opcional do Go
    go_ok = verificar_go()
    if not go_ok:
        log_info("Go não está disponível, mas os testes podem executar apenas com Python")
    
    # Resultado final
    print("\n" + "=" * 60)
    if all(checks):
        log_success("VALIDAÇÃO COMPLETA! O projeto está pronto para uso.")
        print("\nPróximos passos:")
        print("- Windows: scripts\\executar_windows.bat")
        print("- Linux:   scripts/executar_linux.sh")
    else:
        log_error("VALIDAÇÃO FALHOU! Corrija os problemas acima.")
        return False
    
    print("=" * 60)
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
