import sys
import pandas as pd
import numpy as np
import os

if len(sys.argv) < 3:
    print("Uso: python analyze_results.py <caminho_csv> <linguagem>")
    sys.exit(1)

csv_path = sys.argv[1]
language = sys.argv[2].lower()

# Lê o CSV
df = pd.read_csv(csv_path)

# Considera apenas sucessos
df = df[df['status'] == 'sucesso'].copy()



# Remove outliers usando z-score no tempo_total_ms (z <= 2), mas garante que pelo menos 3 execuções de cada cenário não sejam marcadas como outlier

if not df.empty:
    df['is_outlier'] = False
    group_cols = ['num_clientes', 'num_servidores', 'num_mensagens']
    cenarios_limite = []
    def marcar_outliers_grupo(subdf):
        z_scores = np.abs((subdf['tempo_total_ms'] - subdf['tempo_total_ms'].mean()) / subdf['tempo_total_ms'].std(ddof=0))
        outlier_mask = z_scores > 2
        if outlier_mask.sum() > 0:
            idx_ordenado = (z_scores).sort_values().index
            idx_keep = idx_ordenado[:3]
            # Se todas as execuções seriam outlier, registra o cenário
            if outlier_mask.sum() >= (len(subdf) - 3):
                cenarios_limite.append(tuple(subdf.iloc[0][col] for col in group_cols))
            outlier_mask.loc[idx_keep] = False
        return outlier_mask
    # Para evitar DeprecationWarning, removemos as colunas de agrupamento antes do apply
    def marcar_outliers_grupo_sem_grupos(subdf):
        # subdf já contém apenas as linhas do grupo, mas pode conter as colunas de agrupamento
        return marcar_outliers_grupo(subdf.drop(columns=group_cols))
    df['is_outlier'] = df.groupby(group_cols, group_keys=False).apply(marcar_outliers_grupo_sem_grupos)
    if cenarios_limite:
        print("[INFO] Cenários que precisaram da limitação de manter 3 execuções (todas seriam outlier pelo z-score):")
        for c in cenarios_limite:
            print(f"  num_clientes={c[0]}, num_servidores={c[1]}, num_mensagens={c[2]}")
else:
    df['is_outlier'] = False


# Agrupa por cenário e calcula estatísticas SEM outliers, mas mantém todos os cenários
if not df.empty:
    df['throughput_media'] = df['num_mensagens'] / (df['tempo_total_ms'] / 1000)
    group_cols = ['num_clientes', 'num_servidores', 'num_mensagens']
    def stats_sem_outlier(subdf):
        sub = subdf[~subdf['is_outlier']]
        return pd.Series({
            'execucoes': len(sub),
            'tempo_min_ms': sub['tempo_total_ms'].min() if not sub.empty else np.nan,
            'tempo_max_ms': sub['tempo_total_ms'].max() if not sub.empty else np.nan,
            'tempo_media_ms': sub['tempo_total_ms'].mean() if not sub.empty else np.nan,
            'tempo_mediana_ms': sub['tempo_total_ms'].median() if not sub.empty else np.nan,
            'tempo_std_ms': sub['tempo_total_ms'].std(ddof=0) if not sub.empty else np.nan,
            'throughput_min': sub['throughput_media'].min() if not sub.empty else np.nan,
            'throughput_max': sub['throughput_media'].max() if not sub.empty else np.nan,
            'throughput_media': sub['throughput_media'].mean() if not sub.empty else np.nan,
            'throughput_mediana': sub['throughput_media'].median() if not sub.empty else np.nan,
            'throughput_std': sub['throughput_media'].std(ddof=0) if not sub.empty else np.nan
        })
    def stats_sem_outlier_sem_grupos(subdf):
        return stats_sem_outlier(subdf.drop(columns=group_cols))
    stats = df.groupby(group_cols).apply(stats_sem_outlier_sem_grupos).reset_index()
else:
    stats = pd.DataFrame()


# Salva o relatório estatístico
report_path = os.path.join(os.path.dirname(csv_path), f'statistical_report_{language}.csv')
stats.to_csv(report_path, index=False)
print(f"Statistical report saved at: {report_path}")
print(stats.head())
