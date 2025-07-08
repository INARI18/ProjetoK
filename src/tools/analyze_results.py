import sys
import pandas as pd
import numpy as np
import os

if len(sys.argv) < 3:
    print("Uso: python analisar_resultados.py <caminho_csv> <linguagem>")
    sys.exit(1)

csv_path = sys.argv[1]
language = sys.argv[2].lower()

# Lê o CSV
df = pd.read_csv(csv_path)

# Considera apenas sucessos
df = df[df['status'] == 'sucesso'].copy()

# Remove outliers usando z-score no tempo_total_ms
if not df.empty:
    z_scores = np.abs((df['tempo_total_ms'] - df['tempo_total_ms'].mean()) / df['tempo_total_ms'].std(ddof=0))
    df = df[z_scores <= 3]

# Agrupa por cenário (rodada_id, num_clientes, num_servidores, num_mensagens)
# e calcula estatísticas para tempo_total_ms e throughput
if not df.empty:
    df['throughput'] = df['num_mensagens'] / (df['tempo_total_ms'] / 1000)
    group_cols = ['num_clientes', 'num_servidores', 'num_mensagens']
    stats = df.groupby(group_cols).agg(
        execucoes=('tempo_total_ms', 'count'),
        tempo_min_ms=('tempo_total_ms', 'min'),
        tempo_max_ms=('tempo_total_ms', 'max'),
        tempo_media_ms=('tempo_total_ms', 'mean'),
        tempo_mediana_ms=('tempo_total_ms', 'median'),
        tempo_std_ms=('tempo_total_ms', 'std'),
        throughput_min=('throughput', 'min'),
        throughput_max=('throughput', 'max'),
        throughput_media=('throughput', 'mean'),
        throughput_mediana=('throughput', 'median'),
        throughput_std=('throughput', 'std')
    ).reset_index()
else:
    stats = pd.DataFrame()

# Garante que cada cenário seja executado 10 vezes
# (Apenas um aviso, pois a execução paralela deve ser garantida pelo script de testes)
group_cols = ['num_clientes', 'num_servidores', 'num_mensagens']
counts = df.groupby(group_cols).size()
cenarios_incompletos = counts[counts < 10]
if not cenarios_incompletos.empty:
    print("[AVISO] Existem cenários com menos de 10 execuções (após remoção de outliers e falhas):")
    print(cenarios_incompletos)
else:
    print("Todos os cenários possuem pelo menos 10 execuções válidas.")

# Salva o relatório estatístico
report_path = os.path.join(os.path.dirname(csv_path), f'statistical_report_{language}.csv')
stats.to_csv(report_path, index=False)

print(f"Statistical report saved at: {report_path}")
print(stats.head())
