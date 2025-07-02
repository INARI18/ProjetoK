import socket
import argparse
import json
import time

def conectar(host, porta, num_mensagens, cliente_id):
    try:
        cliente = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        cliente.connect((host, porta))
        
        # Enviar múltiplas mensagens conforme configurado
        for i in range(1, num_mensagens + 1):
            msg = {
                "type": "PING",
                "client_id": cliente_id,
                "timestamp": int(time.time() * 1000),
                "sequence": i,
                "data": f"PING {i} do cliente {cliente_id}"
            }
            
            msg_bytes = json.dumps(msg).encode('utf-8')
            
            # Enviar tamanho da mensagem primeiro (protocolo)
            msg_size = f"{len(msg_bytes):08d}".encode('utf-8')
            cliente.sendall(msg_size)
            
            # Enviar a mensagem
            cliente.sendall(msg_bytes)
            
            # Ler resposta
            size_buffer = cliente.recv(8)
            if len(size_buffer) < 8:
                break
                
            response_size = int(size_buffer.decode('utf-8'))
            response_buffer = cliente.recv(response_size)
            
            if len(response_buffer) < response_size:
                break
                
            response = json.loads(response_buffer.decode('utf-8'))
            
            # Pausa mínima entre mensagens (necessária para estabilidade do teste)
            if i < num_mensagens:
                time.sleep(0.005) 
        
        cliente.close()
    except Exception as e:
        pass

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", type=str, required=True)
    parser.add_argument("--porta", type=int, required=True)
    parser.add_argument("--mensagens", type=int, default=1, help="Número de mensagens a enviar")
    parser.add_argument("--cliente-id", type=str, default="", help="ID único do cliente")
    args = parser.parse_args()

    if not args.cliente_id:
        args.cliente_id = f"cliente_{int(time.time() * 1000000)}"

    conectar(args.host, args.porta, args.mensagens, args.cliente_id)
