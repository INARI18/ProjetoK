#!/usr/bin/env python3
"""
Executar Testes Python - ProjetoK
Executa testes completos em Python conforme requisitos da disciplina

IMPORTANTE: Este script foi modificado para rodar APENAS com servidores no Kubernetes.
- Servidores: Executam em pods Kubernetes
- Clientes: Executam localmente, conectam ao service Kubernetes
- Balanceamento: Round-robin automático via service Kubernetes

Pré-requisitos:
1. Cluster Kubernetes rodando
2. kubectl configurado
3. Deployment e Service do servidor criados no cluster
4. Cliente Python na pasta cliente
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

# Obter caminho absoluto da raiz do projeto
SCRIPT_DIR = Path(__file__).parent.absolute()
PROJECT_ROOT = SCRIPT_DIR.parent.parent
SERVIDOR_DIR = PROJECT_ROOT / "src" / "servidor (local)"
CLIENTE_DIR = PROJECT_ROOT / "src" / "cliente (local)"
RESULTADOS_DIR = PROJECT_ROOT / "resultados"

class ExecutorTestePython:
    def __init__(self):
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
        self.KUBERNETES_PORT = 30002  # NodePort para servidor Python
        
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
        
        # 3. Verificar se o cliente Python existe
        cliente_python = CLIENTE_DIR / "cliente.py"
        if not cliente_python.exists():
            print(f"❌ Cliente Python não encontrado: {cliente_python}")
            sys.exit(1)
        else:
            print("✅ Cliente Python encontrado")
        
        # 4. Verificar conectividade com o service Kubernetes
        self._verificar_conectividade_kubernetes()
    
    def _verificar_conectividade_kubernetes(self):
        """Verificar se consegue conectar no service Kubernetes"""
        print(f"🔌 Testando conectividade com {self.KUBERNETES_HOST}:{self.KUBERNETES_PORT}...")
        
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5)
        
        try:
            result = sock.connect_ex((self.KUBERNETES_HOST, self.KUBERNETES_PORT))
            if result == 0:
                print("✅ Conectividade com service Kubernetes OK")
            else:
                raise Exception(f"Não foi possível conectar na porta {self.KUBERNETES_PORT}")
        except Exception as e:
            print(f"❌ Erro de conectividade: {e}")
            print(f"   Certifique-se de que o service Kubernetes está exposto na porta {self.KUBERNETES_PORT}")
            print("   Você pode usar: kubectl port-forward service/servidor-python-service 30002:8000")
            sys.exit(1)
        finally:
            sock.close()
    
    def escalar_deployment(self, num_replicas):
        """Escalar o deployment do servidor Python no Kubernetes"""
        try:
            cmd = ["kubectl", "scale", "deployment", "servidor-python-deployment", 
                   f"--replicas={num_replicas}"]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            
            if result.returncode != 0:
                raise Exception(f"Erro ao escalar: {result.stderr}")
            
            # Aguardar que todos os pods estejam prontos
            print(f"⏳ Aguardando {num_replicas} replicas ficarem prontas...")
            
            for tentativa in range(20):  # 20 segundos de timeout (otimizado)
                cmd_check = ["kubectl", "get", "deployment", "servidor-python-deployment", 
                           "-o", "jsonpath={.status.readyReplicas}"]
                
                result = subprocess.run(cmd_check, capture_output=True, text=True)
                
                if result.returncode == 0:
                    ready_replicas = result.stdout.strip()
                    if ready_replicas == str(num_replicas):
                        print(f"✅ {num_replicas} replicas prontas")
                        return True
                
                time.sleep(1)
            
            raise Exception(f"Timeout aguardando {num_replicas} replicas")
            
        except Exception as e:
            print(f"❌ Erro ao escalar deployment: {e}")
            return False
    
    def executar_cliente_python(self, num_clientes, num_mensagens):
        """Executar múltiplos clientes Python em paralelo"""
        threads = []
        start_time = time.time()
        
        def executar_cliente_individual(cliente_id):
            try:
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
        
        print("🚀 Iniciando execução de testes Python com Kubernetes")
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
            time.sleep(2)
            
            for num_clientes in self.configuracoes['clientes']:
                for num_mensagens in self.configuracoes['mensagens']:
                    for repeticao in range(self.configuracoes['repeticoes']):
                        self.execucao_atual += 1
                        
                        print(f"\n📈 Execução {self.execucao_atual}/{self.total_execucoes}")
                        print(f"   Servidores: {num_servidores}, Clientes: {num_clientes}, "
                              f"Mensagens: {num_mensagens}, Repetição: {repeticao + 1}")
                        
                        # Executar teste
                        tempo_execucao = self.executar_cliente_python(num_clientes, num_mensagens)
                        
                        # Calcular métricas
                        total_mensagens = num_clientes * num_mensagens
                        throughput = total_mensagens / tempo_execucao if tempo_execucao > 0 else 0
                        latencia_media = (tempo_execucao * 1000) / total_mensagens if total_mensagens > 0 else 0
                        
                        resultado = {
                            'timestamp': datetime.now().isoformat(),
                            'linguagem': 'python',
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
        
        arquivo_parcial = RESULTADOS_DIR / "resultados_python_parciais.json"
        
        with open(arquivo_parcial, 'w', encoding='utf-8') as f:
            json.dump(self.resultados, f, indent=2, ensure_ascii=False)
        
        print(f"💾 Resultados parciais salvos: {arquivo_parcial}")
    
    def _salvar_resultados_finais(self):
        """Salvar resultados finais em arquivo JSON"""
        RESULTADOS_DIR.mkdir(exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        arquivo_final = RESULTADOS_DIR / f"resultados_python_k8s_{timestamp}.json"
        
        # Adicionar metadados aos resultados
        dados_finais = {
            'metadados': {
                'data_execucao': datetime.now().isoformat(),
                'total_execucoes': self.total_execucoes,
                'tempo_total': time.time() - self.tempo_inicio,
                'configuracoes': self.configuracoes,
                'ambiente': 'kubernetes',
                'linguagem': 'python'
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
        print("📊 RESUMO FINAL DOS TESTES PYTHON")
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

def main():
    """Função principal"""
    try:
        executor = ExecutorTestePython()
        executor.executar_teste_completo()
        
    except KeyboardInterrupt:
        print("\n⚠️  Execução interrompida pelo usuário")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Erro durante execução: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
