import socket
import csv
import sys
import time
import os
import psutil
import asyncio


async def run_cliente_async(server_host, server_port, num_msgs, num_clientes, cliente_id, num_servidores, cenario_id, repeticao, csv_path, num_clientes_total):
    status_geral = "sucesso"
    erro_geral = ""
    t0_cliente = time.time()
    t0_cliente_str = time.strftime("%Y-%m-%dT%H:%M:%S.") + f"{int((t0_cliente%1)*1e9):09d}"
    process = psutil.Process(os.getpid())
    mem_inicio = process.memory_info().rss
    respostas_recebidas = []
    try:
        reader, writer = await asyncio.open_connection(server_host, server_port)
        for i in range(1, num_msgs+1):
            try:
                writer.write(b"ping\n")
                await writer.drain()
            except Exception as e:
                status_geral = "erro_envio"
                erro_geral = str(e)
                break
        while len(respostas_recebidas) < num_msgs:
            try:
                linha = await reader.readline()
                if not linha:
                    break
                resposta = linha.decode().strip()
                if resposta:
                    respostas_recebidas.append(resposta)
            except Exception as e:
                status_geral = "erro_resposta"
                erro_geral = str(e)
                break
        writer.close()
        await writer.wait_closed()
        for resposta in respostas_recebidas:
            if resposta != "pong":
                status_geral = "falha"
                erro_geral = ";".join(respostas_recebidas)
                break
        if len(respostas_recebidas) < num_msgs and status_geral == "sucesso":
            status_geral = "falha"
            erro_geral = f"Respostas recebidas: {len(respostas_recebidas)}/{num_msgs}"
    except Exception as e:
        status_geral = "erro_conexao"
        erro_geral = str(e)
    t1_cliente = time.time()
    t1_cliente_str = time.strftime("%Y-%m-%dT%H:%M:%S.") + f"{int((t1_cliente%1)*1e9):09d}"
    mem_fim = process.memory_info().rss
    mem_pico = max(mem_inicio, mem_fim)
    mem_mb = mem_pico / 1024 / 1024
    tempo_total_ms = (t1_cliente - t0_cliente) * 1000
    return [
        cenario_id,
        repeticao,
        int(cliente_id),
        num_clientes_total,
        num_servidores,
        num_msgs,
        t0_cliente_str,
        t1_cliente_str,
        f"{tempo_total_ms:.2f}",
        status_geral,
        erro_geral,
        f"{mem_mb:.2f}",
    ]

def main():
    # Parâmetros: host, porta, num_mensagens, num_clientes_host, cliente_idx_inicio, num_servidores, num_clientes_total, cenario_id, repeticao, csv_path
    server_host = sys.argv[1] if len(sys.argv) > 1 else "127.0.0.1"
    server_port = int(sys.argv[2]) if len(sys.argv) > 2 else 9000
    num_msgs = int(sys.argv[3]) if len(sys.argv) > 3 else 10
    num_clientes_host = int(sys.argv[4]) if len(sys.argv) > 4 else 1
    cliente_idx_inicio = int(sys.argv[5]) if len(sys.argv) > 5 else 1
    num_servidores = int(sys.argv[6]) if len(sys.argv) > 6 else 1
    num_clientes_total = int(sys.argv[7]) if len(sys.argv) > 7 else num_clientes_host
    if len(sys.argv) > 8:
        cenario_id = sys.argv[8]
        if not str(cenario_id).startswith("C"):
            cenario_id = f"C{cenario_id}"
    else:
        cenario_id = "C" + time.strftime("%Y%m%dT%H%M%SZ")
    repeticao = int(sys.argv[9]) if len(sys.argv) > 9 else 1
    csv_path = os.environ.get("PYTHON_CSV_TEMP_FILE")
    if not csv_path:
        csv_path = sys.argv[10] if len(sys.argv) > 10 else os.path.join(os.getcwd(), "src", "results", "reports", "test-python.csv")
    # Não cria diretório nenhum, assume que o PowerShell já criou temp-py corretamente

    async def run_all():
        tasks = []
        for i in range(num_clientes_host):
            cliente_id = cliente_idx_inicio + i
            tasks.append(run_cliente_async(server_host, server_port, num_msgs, num_clientes_host, cliente_id, num_servidores, cenario_id, repeticao, csv_path, num_clientes_total))
        resultados = await asyncio.gather(*tasks)
        resultados = list(resultados)
        # Ordena pelo cliente_id numericamente
        # Garante ordenação numérica mesmo se cliente_id vier como string
        resultados.sort(key=lambda x: x[2])
        import fcntl
        with open(csv_path, "a+", newline="") as csv_file:
            fcntl.flock(csv_file, fcntl.LOCK_EX)
            csv_file.seek(0)
            first_line = csv_file.readline()
            write_header = not first_line.startswith("cenario_id")
            csv_file.seek(0, 2)  # Move para o final para append
            writer = csv.writer(csv_file)
            if write_header:
                writer.writerow(["cenario_id","repeticao","cliente_id","num_clientes","num_servidores","num_mensagens","tempo_inicio","tempo_fim","tempo_total_ms","status","erro","mem_mb"])
            for row in resultados:
                writer.writerow(row)
            fcntl.flock(csv_file, fcntl.LOCK_UN)
    asyncio.run(run_all())

if __name__ == "__main__":
    main()
