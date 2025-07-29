# Servidor Python para protocolo Ping-Pong com suporte a múltiplas threads
# Requisitos:
# - Cada conexão de cliente deve ser tratada em uma thread
# - Registrar requisições em CSV
# - Registrar logs de erro
# - Protocolo Ping-Pong: receber 'ping', responder 'pong'

import socket
import threading
import csv
import logging

def handle_client(conn, addr, csv_writer, csv_lock, log):
    with conn:
        buffer = b""
        while True:
            try:
                data = conn.recv(1024)
                if not data:
                    break
                buffer += data
                while b"\n" in buffer:
                    line, buffer = buffer.split(b"\n", 1)
                    msg = line.decode().strip()
                    if msg == "ping":
                        conn.sendall(b"pong\n")
                        with csv_lock:
                            csv_writer.writerow([threading.current_thread().name, addr[0], "ping", "pong", "sucesso"])
                    else:
                        log.error(f"Mensagem inválida de {addr}: {msg}")
            except Exception as e:
                log.error(f"Erro na conexão com {addr}: {e}")
                break


def main():
    import os
    base_dir = os.path.abspath(os.path.dirname(__file__))
    results_dir = os.path.join(base_dir, "results", "reports")
    error_dir = os.path.join(results_dir, "error")
    os.makedirs(error_dir, exist_ok=True)
    os.makedirs(results_dir, exist_ok=True)

    log_path = os.path.join(error_dir, "server_error.log")
    csv_path = os.path.join(results_dir, "server_result.csv")

    logging.basicConfig(filename=log_path, level=logging.ERROR, format="%(asctime)s,%(levelname)s,%(message)s")
    log = logging.getLogger()
    csv_file = open(csv_path, "a", newline="")
    csv_writer = csv.writer(csv_file)
    csv_writer.writerow(["thread", "client_ip", "mensagem_recebida", "mensagem_enviada", "status"])
    csv_lock = threading.Lock()

    # Iniciar servidor TCP
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind(("0.0.0.0", 9000))
        s.listen()
        print("Servidor ouvindo na porta 9000...")
        while True:
            conn, addr = s.accept()
            t = threading.Thread(target=handle_client, args=(conn, addr, csv_writer, csv_lock, log))
            t.daemon = True
            t.start()

if __name__ == "__main__":
    main()
