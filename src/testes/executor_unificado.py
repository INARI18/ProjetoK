#!/usr/bin/env python3
"""
Executor Unificado de Testes - ProjetoK
Este script unifica a execução de testes para Go e Python
Usa exatamente as mesmas configurações e parâmetros para ambas linguagens
Mantém o requisito de 3.000 execuções por linguagem
Otimizado para melhor performance
"""

import os
import sys
import time
import json
import subprocess
import threading
import socket
import statistics
from datetime import datetime
from pathlib import Path
import argparse

# Obter caminho absoluto da raiz do projeto
SCRIPT_DIR = Path(__file__).parent.absolute()
PROJECT_ROOT = SCRIPT_DIR.parent.parent
SERVIDOR_DIR = PROJECT_ROOT / "src" / "servidor (local)"
CLIENTE_DIR = PROJECT_ROOT / "src" / "cliente (local)"
RESULTADOS_DIR = PROJECT_ROOT / "resultados"
RELATORIOS_DIR = RESULTADOS_DIR / "relatorios"

class ExecutorTeste:
    def __init__(self, linguagem="go"):
        self.linguagem = linguagem.lower()
        
        if self.linguagem not in ["go", "python"]:
            raise ValueError("Linguagem deve ser 'go' ou 'python'")
            
        self.configuracoes = {
            'servidores': [2, 4, 6, 8, 10],
            'clientes': [10, 20, 30, 40, 50, 60, 70, 80, 90, 100],
            'mensagens': [1, 10, 100, 500, 1000, 10000],
            'repeticoes': 10
        }
        
        self.total_execucoes = (
            len(self.configuracoes['servidores']) * 
            len(self.configuracoes['clientes']) * 
            len(self.configuracoes['mensagens']) * 
            self.configuracoes['repeticoes']
        )
        
        self.execucao_atual = 0
        self.resultados = []
        self.tempo_inicio = None
        
        # Host do cluster Kubernetes (localhost com NodePort)
        self.KUBERNETES_HOST = "localhost"
        self.KUBERNETES_PORT = 30001 if self.linguagem == "go" else 30002
        self.port_forward_process = None  # Para controlar port-forward se necessário
        
        self._verificar_prerrequisitos()
    
    def _verificar_prerrequisitos(self):
        """Verificar se todos os pré-requisitos estão atendidos"""
        print("🔍 Verificando pré-requisitos...")
        
        # 1. Verificar se kubectl está disponível
        try:
            result = subprocess.run(["kubectl", "version", "--client"], 
                                  capture_output=True, text=True, timeout=10)
            if result.returncode != 0:
                raise Exception("kubectl não está funcionando")
            print("✅ kubectl encontrado e funcionando")
        except Exception as e:
            print(f"❌ Erro com kubectl: {e}")
            print("   Certifique-se de que o kubectl está instalado e configurado")
            sys.exit(1)
        
        # 2. Verificar se o cluster está rodando
        try:
            result = subprocess.run(["kubectl", "cluster-info"], 
                                  capture_output=True, text=True, timeout=10)
            if result.returncode != 0:
                raise Exception("Cluster não está acessível")
            print("✅ Cluster Kubernetes acessível")
        except Exception as e:
            print(f"❌ Erro ao acessar cluster: {e}")
            print("   Certifique-se de que o cluster Kubernetes está rodando")
            sys.exit(1)
        
        # 3. Verificar se o executável/script cliente existe
        if self.linguagem == "go":
            cliente_go = CLIENTE_DIR / "cliente_go.exe"
            if not cliente_go.exists():
                print(f"❌ Executável Go não encontrado: {cliente_go}")
                print("   Compilando cliente Go...")
                self._compilar_cliente_go()
            else:
                print("✅ Executável Go encontrado")
        else:  # python
            cliente_python = CLIENTE_DIR / "cliente.py"
            if not cliente_python.exists():
                print(f"❌ Cliente Python não encontrado: {cliente_python}")
                sys.exit(1)
            else:
                print("✅ Cliente Python encontrado")
        
        # 4. Verificar conectividade com o service Kubernetes
        if not self._verificar_conectividade_kubernetes():
            print("❌ Não foi possível estabelecer conectividade com o service Kubernetes")
            print("   Verifique se os pods estão rodando e o service está funcionando")
            sys.exit(1)
    
    def _compilar_cliente_go(self):
        """Compilar o cliente Go"""
        try:
            os.chdir(CLIENTE_DIR)
            result = subprocess.run(["go", "build", "-o", "cliente_go.exe", "cliente.go"], 
                                  capture_output=True, text=True, timeout=30)
            if result.returncode != 0:
                raise Exception(f"Erro na compilação: {result.stderr}")
            print("✅ Cliente Go compilado com sucesso")
        except Exception as e:
            print(f"❌ Erro ao compilar cliente Go: {e}")
            sys.exit(1)
    
    def _verificar_conectividade_kubernetes(self):
        """Verificar se consegue conectar no service Kubernetes"""
        print(f"🔌 Testando conectividade com {self.KUBERNETES_HOST}:{self.KUBERNETES_PORT}...")
        
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5)
        
        try:
            result = sock.connect_ex((self.KUBERNETES_HOST, self.KUBERNETES_PORT))
            if result == 0:
                print("✅ Conectividade com service Kubernetes OK")
                return True
            else:
                raise Exception(f"Não foi possível conectar na porta {self.KUBERNETES_PORT}")
        except Exception as e:
            print(f"⚠️ NodePort não acessível: {e}")
            if self.linguagem == "go":
                print("🔄 Tentando usar port-forward como alternativa...")
                return self._setup_port_forward()
            else:
                print(f"   Certifique-se de que o service Kubernetes está exposto na porta {self.KUBERNETES_PORT}")
                print("   Você pode usar: kubectl port-forward service/servidor-python-service 30002:8000")
                return False
        finally:
            sock.close()
    
    def _setup_port_forward(self):
        """Configurar port-forward como alternativa ao NodePort (apenas para Go)"""
        try:
            # Iniciar port-forward em background
            cmd = ["kubectl", "port-forward", f"service/servidor-{self.linguagem}-service", f"{self.KUBERNETES_PORT}:8000"]
            self.port_forward_process = subprocess.Popen(
                cmd, 
                stdout=subprocess.PIPE, 
                stderr=subprocess.PIPE,
                creationflags=subprocess.CREATE_NEW_PROCESS_GROUP if os.name == 'nt' else 0
            )
            
            # Aguardar um pouco para o port-forward se estabelecer
            time.sleep(3)
            
            # Testar conectividade novamente
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(5)
            
            try:
                result = sock.connect_ex((self.KUBERNETES_HOST, self.KUBERNETES_PORT))
                if result == 0:
                    print("✅ Port-forward estabelecido com sucesso!")
                    return True
                else:
                    raise Exception("Port-forward não funcionou")
            except Exception as e:
                print(f"❌ Erro com port-forward: {e}")
                if self.port_forward_process:
                    self.port_forward_process.terminate()
                    self.port_forward_process = None
                return False
            finally:
                sock.close()
                
        except Exception as e:
            print(f"❌ Erro ao configurar port-forward: {e}")
            return False
    
    def escalar_deployment(self, num_replicas):
        """Escalar o deployment do servidor no Kubernetes"""
        try:
            cmd = ["kubectl", "scale", "deployment", f"servidor-{self.linguagem}-deployment", 
                   f"--replicas={num_replicas}"]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            
            if result.returncode != 0:
                raise Exception(f"Erro ao escalar: {result.stderr}")
            
            # Aguardar que todos os pods estejam prontos
            print(f"⏳ Aguardando {num_replicas} replicas ficarem prontas...")
            
            # Verificação mais rápida e inteligente
            for tentativa in range(15):  # 15 segundos de timeout (ultra otimizado)
                # Verificar status mais detalhado do deployment
                cmd_check = ["kubectl", "get", "deployment", f"servidor-{self.linguagem}-deployment", 
                           "-o", "jsonpath={.status.readyReplicas},{.status.replicas},{.status.unavailableReplicas}"]
                
                result = subprocess.run(cmd_check, capture_output=True, text=True)
                
                if result.returncode == 0:
                    status_parts = result.stdout.strip().split(',')
                    ready_replicas = status_parts[0] if status_parts[0] else "0"
                    total_replicas = status_parts[1] if len(status_parts) > 1 and status_parts[1] else "0"
                    unavailable = status_parts[2] if len(status_parts) > 2 and status_parts[2] else "0"
                    
                    print(f"   📊 Status: {ready_replicas}/{num_replicas} prontas (unavailable: {unavailable})")
                    
                    if ready_replicas == str(num_replicas) and unavailable in ["", "0"]:
                        print(f"✅ {num_replicas} replicas prontas e estáveis")
                        return True
                
                # Intervalo menor para verificações mais frequentes
                time.sleep(1)
            
            raise Exception(f"Timeout de 15s aguardando {num_replicas} replicas")
            
        except Exception as e:
            print(f"❌ Erro ao escalar deployment: {e}")
            return False
    
    def executar_cliente(self, num_clientes, num_mensagens):
        """Executar múltiplos clientes em paralelo"""
        threads = []
        start_time = time.time()
        
        def executar_cliente_individual(cliente_id):
            try:
                if self.linguagem == "go":
                    cmd = [
                        str(CLIENTE_DIR / "cliente_go.exe"),
                        f"-host={self.KUBERNETES_HOST}",
                        f"-porta={self.KUBERNETES_PORT}",
                        f"-mensagens={num_mensagens}",
                        f"-cliente-id=cliente_go_{cliente_id}"
                    ]
                else:  # python
                    cmd = [
                        "python",
                        str(CLIENTE_DIR / "cliente.py"),
                        f"--host={self.KUBERNETES_HOST}",
                        f"--porta={self.KUBERNETES_PORT}",
                        f"--mensagens={num_mensagens}",
                        f"--cliente-id=cliente_python_{cliente_id}"
                    ]
                
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=15)
                return result.returncode == 0
                
            except Exception:
                return False
        
        # Iniciar todas as threads
        for i in range(num_clientes):
            thread = threading.Thread(target=executar_cliente_individual, args=(i,))
            threads.append(thread)
            thread.start()
        
        # Aguardar todas as threads terminarem
        for thread in threads:
            thread.join()
        
        end_time = time.time()
        return end_time - start_time
    
    def executar_teste_completo(self):
        """Executar todos os testes conforme configuração"""
        self.tempo_inicio = time.time()
        
        print(f"🚀 Iniciando execução de testes {self.linguagem.upper()} com Kubernetes")
        print(f"📊 Total de execuções: {self.total_execucoes}")
        print(f"🎯 Configurações:")
        print(f"   - Servidores: {self.configuracoes['servidores']}")
        print(f"   - Clientes: {self.configuracoes['clientes']}")
        print(f"   - Mensagens: {self.configuracoes['mensagens']}")
        print(f"   - Repetições: {self.configuracoes['repeticoes']}")
        print(f"🌐 Kubernetes: {self.KUBERNETES_HOST}:{self.KUBERNETES_PORT}")
        print("=" * 80)
        
        for num_servidores in self.configuracoes['servidores']:
            print(f"\n🔧 Configurando {num_servidores} servidores...")
            
            if not self.escalar_deployment(num_servidores):
                print(f"❌ Falha ao configurar {num_servidores} servidores. Pulando...")
                continue
            
            # Aguardar estabilização mínima (pods já estão prontos)
            time.sleep(1)
            
            for num_clientes in self.configuracoes['clientes']:
                for num_mensagens in self.configuracoes['mensagens']:
                    for repeticao in range(self.configuracoes['repeticoes']):
                        self.execucao_atual += 1
                        
                        print(f"\n📈 Execução {self.execucao_atual}/{self.total_execucoes}")
                        print(f"   Servidores: {num_servidores}, Clientes: {num_clientes}, "
                              f"Mensagens: {num_mensagens}, Repetição: {repeticao + 1}")
                        
                        # Executar teste
                        tempo_execucao = self.executar_cliente(num_clientes, num_mensagens)
                        
                        # Calcular métricas
                        total_mensagens = num_clientes * num_mensagens
                        throughput = total_mensagens / tempo_execucao if tempo_execucao > 0 else 0
                        latencia_media = (tempo_execucao * 1000) / total_mensagens if total_mensagens > 0 else 0
                        
                        resultado = {
                            'timestamp': datetime.now().isoformat(),
                            'linguagem': self.linguagem,
                            'ambiente': 'kubernetes',
                            'num_servidores': num_servidores,
                            'num_clientes': num_clientes,
                            'num_mensagens': num_mensagens,
                            'repeticao': repeticao + 1,
                            'tempo_execucao': tempo_execucao,
                            'total_mensagens': total_mensagens,
                            'throughput': throughput,
                            'latencia_media': latencia_media
                        }
                        
                        self.resultados.append(resultado)
                        
                        print(f"   ⏱️  Tempo: {tempo_execucao:.3f}s")
                        print(f"   📬 Mensagens: {total_mensagens}")
                        print(f"   🚀 Throughput: {throughput:.2f} msg/s")
                        print(f"   ⚡ Latência média: {latencia_media:.3f}ms")
                        
                        # Salvar resultados parciais a cada 10 execuções
                        if self.execucao_atual % 10 == 0:
                            self._salvar_resultados_parciais()
        
        self._salvar_resultados_finais()
        self._exibir_resumo_final()
    
    def _salvar_resultados_parciais(self):
        """Salvar resultados parciais em arquivo JSON"""
        RESULTADOS_DIR.mkdir(exist_ok=True)
        RELATORIOS_DIR.mkdir(exist_ok=True)
        
        arquivo_parcial = RELATORIOS_DIR / f"resultados_{self.linguagem}_parciais.json"
        
        with open(arquivo_parcial, 'w', encoding='utf-8') as f:
            json.dump(self.resultados, f, indent=2, ensure_ascii=False)
        
        print(f"💾 Resultados parciais salvos: {arquivo_parcial}")
    
    def _salvar_resultados_finais(self):
        """Salvar resultados finais em arquivo JSON"""
        RESULTADOS_DIR.mkdir(exist_ok=True)
        RELATORIOS_DIR.mkdir(exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        arquivo_final = RELATORIOS_DIR / f"resultados_{self.linguagem}_k8s_{timestamp}.json"
        
        # Adicionar metadados aos resultados
        dados_finais = {
            'metadados': {
                'data_execucao': datetime.now().isoformat(),
                'total_execucoes': self.total_execucoes,
                'tempo_total': time.time() - self.tempo_inicio,
                'configuracoes': self.configuracoes,
                'ambiente': 'kubernetes',
                'linguagem': self.linguagem
            },
            'resultados': self.resultados
        }
        
        with open(arquivo_final, 'w', encoding='utf-8') as f:
            json.dump(dados_finais, f, indent=2, ensure_ascii=False)
        
        print(f"💾 Resultados finais salvos: {arquivo_final}")
        return arquivo_final
    
    def _exibir_resumo_final(self):
        """Exibir resumo final dos testes"""
        tempo_total = time.time() - self.tempo_inicio
        
        print("\n" + "=" * 80)
        print(f"📊 RESUMO FINAL DOS TESTES {self.linguagem.upper()}")
        print("=" * 80)
        print(f"✅ Execuções concluídas: {len(self.resultados)}/{self.total_execucoes}")
        print(f"⏱️  Tempo total: {tempo_total:.2f} segundos ({tempo_total/60:.1f} minutos)")
        
        if self.resultados:
            throughputs = [r['throughput'] for r in self.resultados if r['throughput'] > 0]
            latencias = [r['latencia_media'] for r in self.resultados if r['latencia_media'] > 0]
            
            if throughputs:
                print(f"🚀 Throughput médio: {statistics.mean(throughputs):.2f} msg/s")
                print(f"🚀 Throughput máximo: {max(throughputs):.2f} msg/s")
            
            if latencias:
                print(f"⚡ Latência média: {statistics.mean(latencias):.3f}ms")
                print(f"⚡ Latência mínima: {min(latencias):.3f}ms")
        
        print("=" * 80)

    def _cleanup(self):
        """Limpeza de recursos"""
        if self.port_forward_process:
            print("🧹 Terminando port-forward...")
            try:
                self.port_forward_process.terminate()
                self.port_forward_process.wait(timeout=5)
            except:
                try:
                    self.port_forward_process.kill()
                except:
                    pass
            self.port_forward_process = None

def main():
    """Função principal"""
    parser = argparse.ArgumentParser(description='Executor Unificado de Testes - ProjetoK')
    parser.add_argument('--linguagem', type=str, default="go", choices=["go", "python"],
                        help='Linguagem a ser testada (go ou python)')
    args = parser.parse_args()
    
    executor = None
    try:
        executor = ExecutorTeste(linguagem=args.linguagem)
        executor.executar_teste_completo()
        
    except KeyboardInterrupt:
        print("\n⚠️  Execução interrompida pelo usuário")
        if executor:
            executor._cleanup()
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Erro durante execução: {e}")
        if executor:
            executor._cleanup()
        sys.exit(1)
    finally:
        if executor:
            executor._cleanup()

if __name__ == "__main__":
    main()
