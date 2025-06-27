import subprocess
import time
import csv
import os
import random
import glob
from concurrent.futures import ThreadPoolExecutor
from graficos import gerar_graficos, gerar_graficos_individuais_por_mensagem
from analise_estatistica import calcular_estatisticas_avancadas

# Configurações de teste
SERVIDOR_CMD = "python ../servidor/servidor.py --porta {}"
CLIENTE_PYTHON_CMD = "python ../cliente/cliente.py --host 127.0.0.1 --porta {} --mensagens {} --cliente-id {}"
CLIENTE_GO_CMD = "../cliente/cliente --host=127.0.0.1 --porta={} --mensagens={} --cliente-id={}"
PORTA_BASE = 8000

servidores_processos = []
CSV_SAIDA = "../../resultados/csv/resultados_teste_carga.csv"

def limpar_arquivos_antigos():
    """Remove arquivos de resultado anteriores para evitar confusão"""
    arquivos_para_limpar = [
        "../../resultados/csv/resultados_teste_carga.csv",
        "../../resultados/csv/requests_consolidado.csv",
        "../../resultados/csv/requests_porta_*.csv",
        "../../resultados/graficos/analise_performance.png",
        "../../resultados/relatorios/relatorio_detalhado.csv",
        "../../resultados/csv/comparacao_linguagens.csv",
        "../../resultados/relatorios/resumo_executivo.csv"
    ]
    
    print("Limpando arquivos de execuções anteriores...")
    for pattern in arquivos_para_limpar:
        for arquivo in glob.glob(pattern):
            try:
                os.remove(arquivo)
                print(f"Removido: {arquivo}")
            except OSError:
                pass

def compilar_cliente_go():
    """Compila o cliente Go se necessário"""
    # Lista de possíveis comandos Go
    go_commands = [
        "go",  # Se estiver no PATH
        r"C:\Program Files\Go\bin\go.exe",  # Local padrão Windows
        r"C:\Go\bin\go.exe",  # Local alternativo Windows
        "/usr/local/go/bin/go",  # Local padrão Linux/macOS
        "/usr/bin/go",  # Local alternativo Linux
    ]
    
    try:
        if not os.path.exists("../cliente/cliente.exe") and not os.path.exists("../cliente/cliente"):
            print("Compilando cliente Go...")
            
            # Tentar cada comando Go até encontrar um que funcione
            for go_cmd in go_commands:
                try:
                    if os.path.exists(go_cmd) or go_cmd == "go":
                        if os.name == 'nt':  # Windows
                            subprocess.run([go_cmd, "build", "-o", "cliente.exe", "cliente.go"], 
                                         check=True, cwd="../cliente", capture_output=True)
                        else:  # Linux/macOS
                            subprocess.run([go_cmd, "build", "-o", "cliente", "cliente.go"], 
                                         check=True, cwd="../cliente", capture_output=True)
                        print(f"Cliente Go compilado com sucesso usando: {go_cmd}")
                        return True
                except (subprocess.CalledProcessError, FileNotFoundError):
                    continue
            
            print("Erro: Nenhum comando Go funcional encontrado")
            return False
        return True
    except Exception as e:
        print(f"Erro ao compilar cliente Go: {e}")
        return False

def iniciar_servidores(qtd_servidores):
    for i in range(qtd_servidores):
        porta = PORTA_BASE + i
        proc = subprocess.Popen(SERVIDOR_CMD.format(porta).split(),
                                stdout=subprocess.DEVNULL,
                                stderr=subprocess.DEVNULL)
        servidores_processos.append(proc)
        time.sleep(0.5)

def encerrar_servidores():
    for proc in servidores_processos:
        proc.terminate()
        proc.wait()
    servidores_processos.clear()

def cliente_worker(porta, num_mensagens, cliente_id, usar_go=False):
    inicio = time.time()
    try:
        if usar_go and os.path.exists("../cliente/cliente.exe"):
            cmd = CLIENTE_GO_CMD.format(porta, num_mensagens, cliente_id).split()
        elif usar_go and os.path.exists("../cliente/cliente"):
            cmd = CLIENTE_GO_CMD.format(porta, num_mensagens, cliente_id).split()
        else:
            cmd = CLIENTE_PYTHON_CMD.format(porta, num_mensagens, cliente_id).split()
        
        subprocess.run(cmd, timeout=30, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        duracao = time.time() - inicio
        return duracao, True
    except Exception:
        return None, False

def testar_carga(qtd_servidores, qtd_clientes, num_mensagens, writer):
    print(f"\n>>> Teste com {qtd_servidores} servidores, {qtd_clientes} clientes e {num_mensagens} mensagens")

    iniciar_servidores(qtd_servidores)
    time.sleep(3)  # Aguardar servidores iniciarem

    tempos = []
    erros = 0
    usar_go = random.choice([True, False])  # Alternar entre Python e Go

    portas = [PORTA_BASE + i for i in range(qtd_servidores)]

    with ThreadPoolExecutor(max_workers=min(qtd_clientes, 50)) as executor:
        futuros = []
        for i in range(qtd_clientes):
            porta = portas[i % qtd_servidores]
            cliente_id = f"cliente_{i}_{int(time.time() * 1000)}"
            futuros.append(executor.submit(cliente_worker, porta, num_mensagens, cliente_id, usar_go))

        for futuro in futuros:
            duracao, sucesso = futuro.result()
            if sucesso:
                tempos.append(duracao)
            else:
                erros += 1

    media = sum(tempos) / len(tempos) if tempos else 0
    throughput = (len(tempos) * num_mensagens) / media if media > 0 else 0
    linguagem = "Go" if usar_go else "Python"
    
    print(f"-> Linguagem: {linguagem} | Media: {media:.3f}s | Throughput: {throughput:.2f} req/s | Sucesso: {len(tempos)} | Erros: {erros}")

    # Salva no CSV com mais detalhes
    writer.writerow([
        qtd_servidores, qtd_clientes, num_mensagens, linguagem,
        f"{media:.3f}", f"{throughput:.2f}", len(tempos), erros
    ])
    
    encerrar_servidores()
    time.sleep(2)  # Pausa entre testes

if __name__ == "__main__":
    # Limpar arquivos anteriores
    limpar_arquivos_antigos()
    
    # Tentar compilar cliente Go
    go_disponivel = compilar_cliente_go()
    
    with open(CSV_SAIDA, mode="w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([
            "Servidores", "Clientes", "Mensagens", "Linguagem", 
            "Tempo Médio (s)", "Throughput (req/s)", "Sucessos", "Erros"
        ])

        # Cenários de teste CONFORME ESPECIFICAÇÃO EXATA:
        # 5 servidores × 10 clientes × 6 mensagens × 10 repetições = 3000 execuções
        
        configuracoes_teste = []
        for servidores in range(2, 11, 2):        # 2, 4, 6, 8, 10 servidores
            for clientes in range(10, 101, 10):   # 10, 20, ..., 100 clientes
                for mensagens in [1, 10, 100, 500, 1000, 10000]:  # 6 tipos de mensagem EXATOS
                    configuracoes_teste.append((servidores, clientes, mensagens))
        
        total_execucoes = len(configuracoes_teste) * 10
        execucao_atual = 0
        
        print(f"Iniciando {total_execucoes} execuções ({len(configuracoes_teste)} configurações × 10 repetições)")
        
        for servidores, clientes, mensagens in configuracoes_teste:
            for repeticao in range(10):   # 10 repetições por configuração
                execucao_atual += 1
                print(f"Execução {execucao_atual}/{total_execucoes} - {servidores}S {clientes}C {mensagens}M (repetição {repeticao + 1}/10)")
                testar_carga(servidores, clientes, mensagens, writer)
                time.sleep(0.5)  # Pausa menor entre repetições

    print(f"\nResultados salvos em '{CSV_SAIDA}'")
    print("Gerando gráficos individuais por cenário de mensagens...")
    
    # Gerar gráficos individuais por cenário de mensagens
    gerar_graficos_individuais_por_mensagem()
    
    print("Gerando gráfico consolidado...")
    # Gerar gráficos dos resultados
    gerar_graficos()
    
    # Executar análise estatística avançada
    print("Executando análise estatística avançada...")
    calcular_estatisticas_avancadas()
    
    # Exibir resumo dos arquivos gerados
    print("\n=== ARQUIVOS GERADOS ===")
    arquivos_resultado = [
        "../../resultados/csv/resultados_teste_carga.csv",
        "../../resultados/csv/requests_consolidado.csv", 
        "../../resultados/graficos/analise_performance.png",
        "../../resultados/relatorios/relatorio_detalhado.csv",
        "../../resultados/csv/comparacao_linguagens.csv",
        "../../resultados/relatorios/resumo_executivo.csv"
    ]
    
    for arquivo in arquivos_resultado:
        if os.path.exists(arquivo):
            tamanho = os.path.getsize(arquivo)
            print(f"✓ {arquivo} ({tamanho:,} bytes)")
        else:
            print(f"✗ {arquivo} (não gerado)")
    
    print(f"\nTotal de cenários testados: 3000 (300 configurações × 10 repetições)")
    print("Análise completa disponível em: analise_performance.png")
