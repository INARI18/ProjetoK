#!/usr/bin/env python3
"""
Teste de Carga - ProjetoK
Teste rápido para validar o funcionamento dos servidores Kubernetes
"""

import time
import json
import subprocess
import threading
import socket
from pathlib import Path
from datetime import datetime

# Obter caminho absoluto da raiz do projeto
SCRIPT_DIR = Path(__file__).parent.absolute()
PROJECT_ROOT = SCRIPT_DIR.parent.parent
CLIENTE_DIR = PROJECT_ROOT / "src" / "cliente (local)"

class TesteCarga:
    def __init__(self):
        self.KUBERNETES_HOST = "localhost"
        self.KUBERNETES_PORT_GO = 30001
        self.KUBERNETES_PORT_PYTHON = 30002
        
        self._verificar_prerrequisitos()
    
    def _verificar_prerrequisitos(self):
        """Verificar pré-requisitos básicos"""
        print("🔍 Verificando pré-requisitos...")
        
        # Verificar kubectl
        try:
            result = subprocess.run(["kubectl", "version", "--client"], 
                                  capture_output=True, text=True, timeout=10)
            if result.returncode != 0:
                raise Exception("kubectl não funcionando")
            print("✅ kubectl OK")
        except Exception as e:
            print(f"❌ Erro kubectl: {e}")
            return False
        
        # Verificar executável Go
        cliente_go = CLIENTE_DIR / "cliente_go.exe"
        if not cliente_go.exists():
            print("⚠️  Cliente Go não encontrado, compilando...")
            self._compilar_cliente_go()
        else:
            print("✅ Cliente Go OK")
        
        # Verificar cliente Python
        cliente_python = CLIENTE_DIR / "cliente.py"
        if not cliente_python.exists():
            print("❌ Cliente Python não encontrado")
            return False
        else:
            print("✅ Cliente Python OK")
        
        return True
    
    def _compilar_cliente_go(self):
        """Compilar cliente Go"""
        try:
            import os
            os.chdir(CLIENTE_DIR)
            result = subprocess.run(["go", "build", "-o", "cliente_go.exe", "cliente.go"], 
                                  capture_output=True, text=True, timeout=30)
            if result.returncode != 0:
                print(f"❌ Erro compilação Go: {result.stderr}")
                return False
            print("✅ Cliente Go compilado")
            return True
        except Exception as e:
            print(f"❌ Erro ao compilar Go: {e}")
            return False
    
    def _testar_conectividade(self, host, port, nome):
        """Testar conectividade com servidor"""
        print(f"🔌 Testando {nome} em {host}:{port}...")
        
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5)
        
        try:
            result = sock.connect_ex((host, port))
            if result == 0:
                print(f"✅ {nome} acessível")
                return True
            else:
                print(f"❌ {nome} não acessível (porta {port})")
                return False
        except Exception as e:
            print(f"❌ Erro {nome}: {e}")
            return False
        finally:
            sock.close()
    
    def _executar_cliente_go(self, num_clientes=5, num_mensagens=10):
        """Testar cliente Go"""
        print(f"🔥 Testando Go: {num_clientes} clientes, {num_mensagens} mensagens cada")
        
        threads = []
        sucessos = 0
        falhas = 0
        
        def executar_cliente_individual(cliente_id):
            nonlocal sucessos, falhas
            try:
                cmd = [
                    str(CLIENTE_DIR / "cliente_go.exe"),
                    f"-host={self.KUBERNETES_HOST}",
                    f"-porta={self.KUBERNETES_PORT_GO}",
                    f"-mensagens={num_mensagens}",
                    f"-cliente-id=teste_go_{cliente_id}"
                ]
                
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
                if result.returncode == 0:
                    sucessos += 1
                else:
                    falhas += 1
                    
            except Exception:
                falhas += 1
        
        start_time = time.time()
        
        # Iniciar clientes
        for i in range(num_clientes):
            thread = threading.Thread(target=executar_cliente_individual, args=(i,))
            threads.append(thread)
            thread.start()
        
        # Aguardar conclusão
        for thread in threads:
            thread.join()
        
        end_time = time.time()
        tempo_total = end_time - start_time
        
        print(f"   ⏱️  Tempo: {tempo_total:.3f}s")
        print(f"   ✅ Sucessos: {sucessos}")
        print(f"   ❌ Falhas: {falhas}")
        
        return sucessos > 0
    
    def _executar_cliente_python(self, num_clientes=5, num_mensagens=10):
        """Testar cliente Python"""
        print(f"🐍 Testando Python: {num_clientes} clientes, {num_mensagens} mensagens cada")
        
        threads = []
        sucessos = 0
        falhas = 0
        
        def executar_cliente_individual(cliente_id):
            nonlocal sucessos, falhas
            try:
                cmd = [
                    "python",
                    str(CLIENTE_DIR / "cliente.py"),
                    f"--host={self.KUBERNETES_HOST}",
                    f"--porta={self.KUBERNETES_PORT_PYTHON}",
                    f"--mensagens={num_mensagens}",
                    f"--cliente-id=teste_python_{cliente_id}"
                ]
                
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
                if result.returncode == 0:
                    sucessos += 1
                else:
                    falhas += 1
                    
            except Exception:
                falhas += 1
        
        start_time = time.time()
        
        # Iniciar clientes
        for i in range(num_clientes):
            thread = threading.Thread(target=executar_cliente_individual, args=(i,))
            threads.append(thread)
            thread.start()
        
        # Aguardar conclusão
        for thread in threads:
            thread.join()
        
        end_time = time.time()
        tempo_total = end_time - start_time
        
        print(f"   ⏱️  Tempo: {tempo_total:.3f}s")
        print(f"   ✅ Sucessos: {sucessos}")
        print(f"   ❌ Falhas: {falhas}")
        
        return sucessos > 0
    
    def executar_teste_completo(self):
        """Executar teste de carga completo"""
        print("🚀 TESTE DE CARGA - PROJETO K")
        print("=" * 50)
        
        # Verificar conectividade
        go_ok = self._testar_conectividade(self.KUBERNETES_HOST, self.KUBERNETES_PORT_GO, "Servidor Go")
        python_ok = self._testar_conectividade(self.KUBERNETES_HOST, self.KUBERNETES_PORT_PYTHON, "Servidor Python")
        
        if not go_ok and not python_ok:
            print("\n❌ Nenhum servidor acessível!")
            print("   Verifique se os deployments Kubernetes estão rodando")
            print("   Use: kubectl get pods")
            return False
        
        print("\n" + "=" * 50)
        
        # Testar Go se disponível
        if go_ok:
            try:
                go_sucesso = self._executar_cliente_go()
                if go_sucesso:
                    print("✅ Teste Go: PASSOU")
                else:
                    print("❌ Teste Go: FALHOU")
            except Exception as e:
                print(f"❌ Erro teste Go: {e}")
                go_sucesso = False
        else:
            go_sucesso = False
            print("⚠️  Teste Go: PULADO (servidor indisponível)")
        
        print()
        
        # Testar Python se disponível
        if python_ok:
            try:
                python_sucesso = self._executar_cliente_python()
                if python_sucesso:
                    print("✅ Teste Python: PASSOU")
                else:
                    print("❌ Teste Python: FALHOU")
            except Exception as e:
                print(f"❌ Erro teste Python: {e}")
                python_sucesso = False
        else:
            python_sucesso = False
            print("⚠️  Teste Python: PULADO (servidor indisponível)")
        
        print("\n" + "=" * 50)
        print("📊 RESUMO DO TESTE DE CARGA")
        print("=" * 50)
        
        if go_sucesso and python_sucesso:
            print("🎉 TODOS OS TESTES PASSARAM!")
            print("   O sistema está funcionando corretamente")
            print("   Pronto para executar os testes completos")
        elif go_sucesso or python_sucesso:
            print("⚠️  ALGUNS TESTES PASSARAM")
            print("   Verifique os servidores que falharam")
        else:
            print("❌ TODOS OS TESTES FALHARAM!")
            print("   Verifique a configuração do Kubernetes")
        
        print("\n💡 Próximos passos:")
        if go_sucesso and python_sucesso:
            print("   - Execute: scripts\\executar_testes_go.bat")
            print("   - Execute: scripts\\executar_testes_python.bat")
            print("   - Execute: scripts\\gerar_graficos.bat")
        else:
            print("   - Execute: scripts\\deploy_kubernetes.bat")
            print("   - Verifique: kubectl get pods")
            print("   - Execute este teste novamente")
        
        return go_sucesso and python_sucesso

def main():
    """Função principal"""
    try:
        teste = TesteCarga()
        teste.executar_teste_completo()
        
    except KeyboardInterrupt:
        print("\n⚠️  Teste interrompido pelo usuário")
    except Exception as e:
        print(f"\n❌ Erro durante teste: {e}")

if __name__ == "__main__":
    main()
