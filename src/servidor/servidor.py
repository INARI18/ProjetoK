import socket
import argparse
import threading
import json
import time
import csv
import os
from datetime import datetime

# Lock para acesso seguro ao arquivo CSV
csv_lock = threading.Lock()

def registrar_requisicao(client_id, sequence, timestamp_req, timestamp_resp, status, porta):
    """Registra a requisição no arquivo CSV"""
    with csv_lock:
        arquivo_csv = f"requests_porta_{porta}.csv"
        arquivo_existe = os.path.exists(arquivo_csv)
        
        with open(arquivo_csv, 'a', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            if not arquivo_existe:
                writer.writerow([
                    'timestamp_request', 'timestamp_response', 'client_id', 
                    'sequence', 'response_time_ms', 'status', 'server_port'
                ])
            
            response_time = timestamp_resp - timestamp_req
            writer.writerow([
                timestamp_req, timestamp_resp, client_id, sequence, 
                response_time, status, porta
            ])

def lidar_com_cliente(conn, addr, porta_servidor):
    try:
        while True:
            # Ler tamanho da mensagem (protocolo)
            size_buffer = conn.recv(8)
            if len(size_buffer) < 8:
                break
                
            msg_size = int(size_buffer.decode('utf-8'))
            
            # Ler a mensagem completa
            msg_buffer = conn.recv(msg_size)
            if len(msg_buffer) < msg_size:
                break
                
            timestamp_recebido = int(time.time() * 1000)
            
            try:
                message = json.loads(msg_buffer.decode('utf-8'))
                
                # Implementar protocolo PING
                msg_type = message.get('type', '').upper()
                
                if msg_type == 'PING':
                    # Protocolo PING: responde com PONG + timestamp original
                    response = {
                        "type": "PONG",
                        "status": "success",
                        "timestamp": int(time.time() * 1000),
                        "original_timestamp": message.get('timestamp', timestamp_recebido),
                        "client_id": message.get('client_id'),
                        "sequence": message.get('sequence', 0),
                        "message": f"PONG para {message.get('client_id', 'unknown')}"
                    }
                else:
                    # Protocolo genérico para outras mensagens
                    response = {
                        "type": "response",
                        "status": "success", 
                        "timestamp": int(time.time() * 1000),
                        "message": f"Processado: {message.get('data', '')}"
                    }
                
                # Registrar no CSV
                registrar_requisicao(
                    message.get('client_id', 'unknown'),
                    message.get('sequence', 0),
                    message.get('timestamp', timestamp_recebido),
                    response['timestamp'],
                    'success',
                    porta_servidor
                )
                
            except json.JSONDecodeError:
                response = {
                    "type": "response",
                    "status": "error",
                    "timestamp": int(time.time() * 1000),
                    "message": "Erro ao decodificar mensagem"
                }
                
                registrar_requisicao(
                    'unknown', 0, timestamp_recebido, 
                    response['timestamp'], 'error', porta_servidor
                )
            
            # Enviar resposta
            response_bytes = json.dumps(response).encode('utf-8')
            response_size = f"{len(response_bytes):08d}".encode('utf-8')
            
            conn.sendall(response_size)
            conn.sendall(response_bytes)
            
    except Exception as e:
        # Registrar erro de conexão
        timestamp_erro = int(time.time() * 1000)
        registrar_requisicao(
            'unknown', 0, timestamp_erro, timestamp_erro, 
            f'connection_error: {str(e)}', porta_servidor
        )
    finally:
        conn.close()

def iniciar_servidor(porta):
    servidor = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    servidor.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    servidor.bind(("0.0.0.0", porta))
    servidor.listen()

    print(f"[SERVIDOR] Escutando na porta {porta}")

    try:
        while True:
            conn, addr = servidor.accept()
            # Uma thread por cliente conforme requisito
            thread = threading.Thread(target=lidar_com_cliente, args=(conn, addr, porta))
            thread.daemon = True
            thread.start()
    except KeyboardInterrupt:
        print("Encerrando servidor...")
    finally:
        servidor.close()

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--porta", type=int, required=True)
    args = parser.parse_args()

    iniciar_servidor(args.porta)
