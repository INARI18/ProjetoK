import socket
import argparse
import threading
import json
import time
from datetime import datetime

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
                
            except json.JSONDecodeError:
                response = {
                    "type": "response",
                    "status": "error",
                    "timestamp": int(time.time() * 1000),
                    "message": "Erro ao decodificar mensagem"
                }
            
            # Enviar resposta
            response_bytes = json.dumps(response).encode('utf-8')
            response_size = f"{len(response_bytes):08d}".encode('utf-8')
            
            conn.sendall(response_size)
            conn.sendall(response_bytes)
            
    except Exception as e:
        print(f"Erro na conexão: {e}")
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
            # Uma thread por cliente
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
