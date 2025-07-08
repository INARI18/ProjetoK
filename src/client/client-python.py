import socket
import csv
import sys
import time
import os
from filelock import FileLock

def main():
    try:
        # Parâmetros: host, porta, num_mensagens, num_clientes, cliente_id, num_servidores, rodada_id, repeticao
        server_host = sys.argv[1] if len(sys.argv) > 1 else "127.0.0.1"
        server_port = int(sys.argv[2]) if len(sys.argv) > 2 else 9000
        num_msgs = int(sys.argv[3]) if len(sys.argv) > 3 else 10
        num_clientes = int(sys.argv[4]) if len(sys.argv) > 4 else 1
        cliente_id = int(sys.argv[5]) if len(sys.argv) > 5 else 1
        num_servidores = int(sys.argv[6]) if len(sys.argv) > 6 else 1
        rodada_id = f"R{sys.argv[7]}" if len(sys.argv) > 7 else time.strftime("%Y%m%dT%H%M%SZ")
        repeticao = int(sys.argv[8]) if len(sys.argv) > 8 else 1

        # Caminho absoluto para garantir que o CSV fique sempre em src/results/reports/
        csv_path = os.path.join(os.getcwd(), "src", "results", "reports", "test-python.csv")
        os.makedirs(os.path.dirname(csv_path), exist_ok=True)
        lock_path = csv_path + ".lock"
        status_geral = "sucesso"
        erro_geral = ""
        t0_cliente = time.time()
        t0_cliente_str = time.strftime("%Y-%m-%dT%H:%M:%S.") + f"{int((t0_cliente%1)*1e9):09d}"
        try:
            with socket.create_connection((server_host, server_port), timeout=5) as s:
                for i in range(1, num_msgs+1):
                    try:
                        s.sendall(b"ping\n")
                        data = s.recv(1024)
                        resposta = data.decode().strip()
                        if resposta != "pong":
                            status_geral = "falha"
                            erro_geral = resposta
                            break
                    except Exception as e:
                        status_geral = "erro"
                        erro_geral = str(e)
                        break
        except Exception as e:
            status_geral = "erro_conexao"
            erro_geral = str(e)
        t1_cliente = time.time()
        t1_cliente_str = time.strftime("%Y-%m-%dT%H:%M:%S.") + f"{int((t1_cliente%1)*1e9):09d}"
        tempo_total_ms = (t1_cliente - t0_cliente) * 1000

        # Escreve no CSV com lock
        with FileLock(lock_path):
            write_header = not os.path.exists(csv_path) or os.path.getsize(csv_path) == 0
            with open(csv_path, "a", newline="") as csv_file:
                writer = csv.writer(csv_file)
                if write_header:
                    writer.writerow(["rodada_id","repeticao","cliente_id","num_clientes","num_servidores","num_mensagens","tempo_inicio","tempo_fim","tempo_total_ms","status","erro"])
                writer.writerow([
                    rodada_id,
                    repeticao,
                    cliente_id,
                    num_clientes,
                    num_servidores,
                    num_msgs,
                    t0_cliente_str,
                    t1_cliente_str,
                    f"{tempo_total_ms:.2f}",
                    status_geral,
                    erro_geral
                ])
    except KeyboardInterrupt:
        # Silencia o traceback ao receber Ctrl+C
        pass

if __name__ == "__main__":
    main()
