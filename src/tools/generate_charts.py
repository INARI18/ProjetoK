import os
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

# Caminhos dos relatórios
reports_dir = os.path.join(os.path.dirname(__file__), '..', 'results', 'reports')
charts_dir = os.path.join(os.path.dirname(__file__), '..', 'results', 'charts')
os.makedirs(charts_dir, exist_ok=True)

files = {
    'Go': os.path.join(reports_dir, 'statistical_report_go.csv'),
    'Python': os.path.join(reports_dir, 'statistical_report_python.csv')
}

data = {}
for lang, path in files.items():
    if os.path.exists(path):
        data[lang] = pd.read_csv(path)
    else:
        print(f"[AVISO] Relatório não encontrado para {lang}: {path}")

if not data:
    print("Nenhum relatório encontrado. Gere os relatórios estatísticos antes de rodar este script.")
    exit(1)

# --- Radar de métricas avançadas de desempenho ---
# 1. Escalabilidade: throughput com max clientes / throughput com min clientes (fixando servidores e mensagens)
# 2. Eficiência relativa: throughput com max clientes / (max clientes × throughput com min clientes)
# 3. Consistência: 1 - (std/mean do tempo de resposta global)
# 4. Tempo de resposta por mensagem: menor valor entre Go e Python dividido pelo valor da linguagem
# 5. Speedup: tempo com 2 servidores / tempo com max servidores (fixando clientes e mensagens)
# 6. Overhead: (tempo com max clientes - tempo com min clientes) / (max clientes - min clientes)

advanced_labels = [
    'Escalabilidade',
    'Eficiência Relativa',
    'Consistência (DPR)',
    'Resp. por Mensagem',
    'Speedup',
    'Overhead'
]

adv_stats = {}
for lang, df in data.items():
    # 1. Escalabilidade
    min_cli = df['num_clientes'].min()
    max_cli = df['num_clientes'].max()
    filtro = (df['num_servidores'] == df['num_servidores'].min()) & (df['num_mensagens'] == df['num_mensagens'].min())
    tput_min = df.loc[filtro & (df['num_clientes'] == min_cli), 'throughput_media'].mean()
    tput_max = df.loc[filtro & (df['num_clientes'] == max_cli), 'throughput_media'].mean()
    escalabilidade = tput_max / tput_min if tput_min else 0
    # 2. Eficiência relativa
    eficiencia = tput_max / (max_cli * tput_min) if tput_min and max_cli else 0
    # 3. Consistência (Desvio Padrão Relativo invertido)
    dpr = df['tempo_media_ms'].std() / df['tempo_media_ms'].mean() if df['tempo_media_ms'].mean() else 0
    consistencia = 1 / (1 + dpr) if dpr >= 0 else 0
    # 4. Tempo de resposta por mensagem (menor é melhor, normalizado depois)
    resp_msg = df['tempo_media_ms'].mean() / df['num_mensagens'].mean() if df['num_mensagens'].mean() else 0
    # 5. Speedup
    min_srv = df['num_servidores'].min()
    max_srv = df['num_servidores'].max()
    filtro_srv = (df['num_clientes'] == min_cli) & (df['num_mensagens'] == df['num_mensagens'].min())
    tempo_min_srv = df.loc[filtro_srv & (df['num_servidores'] == min_srv), 'tempo_media_ms'].mean()
    tempo_max_srv = df.loc[filtro_srv & (df['num_servidores'] == max_srv), 'tempo_media_ms'].mean()
    speedup = tempo_min_srv / tempo_max_srv if tempo_max_srv else 0
    # 6. Overhead
    overhead = (df.loc[filtro & (df['num_clientes'] == max_cli), 'tempo_media_ms'].mean() - df.loc[filtro & (df['num_clientes'] == min_cli), 'tempo_media_ms'].mean()) / (max_cli - min_cli) if (max_cli - min_cli) else 0
    adv_stats[lang] = [escalabilidade, eficiencia, consistencia, resp_msg, speedup, overhead]

# Normalização: para cada métrica, quanto mais próximo de 1, melhor
# Para tempo de resposta por mensagem e overhead, menor é melhor, então normaliza invertendo
adv_array = np.array(list(adv_stats.values()))
adv_norm = []
for i in range(len(advanced_labels)):
    vals = adv_array[:, i]
    if advanced_labels[i] in ['Resp. por Mensagem', 'Overhead']:
        best = vals.min()
        norm = best / vals
    elif advanced_labels[i] == 'Consistência (DPR)':
        # Consistência: maior é melhor, normalização direta
        best = vals.max()
        norm = vals / best if best else np.zeros_like(vals)
    else:
        best = vals.max()
        norm = vals / best if best else np.zeros_like(vals)
    adv_norm.append(norm)
adv_norm = np.array(adv_norm).T  # shape: (2, 6)

# Fecha o círculo
adv_norm_go = adv_norm[0].tolist() + [adv_norm[0][0]]
adv_norm_py = adv_norm[1].tolist() + [adv_norm[1][0]]
angles_adv = np.linspace(0, 2 * np.pi, len(advanced_labels), endpoint=False).tolist()
angles_adv += angles_adv[:1]

plt.figure(figsize=(8,8))
ax = plt.subplot(111, polar=True)
ax.plot(angles_adv, adv_norm_go, label='Go', linewidth=2, color='tab:blue')
ax.fill(angles_adv, adv_norm_go, alpha=0.15, color='tab:blue')
ax.plot(angles_adv, adv_norm_py, label='Python', linewidth=2, color='tab:orange')
ax.fill(angles_adv, adv_norm_py, alpha=0.15, color='tab:orange')

ax.set_thetagrids(np.degrees(angles_adv[:-1]), advanced_labels, fontsize=11)
ax.set_yticklabels([])
ax.set_title('Radar de métricas avançadas de desempenho', size=14, pad=20)
ax.legend(loc='upper right', bbox_to_anchor=(1.2, 1.1))
plt.tight_layout()
plt.savefig(os.path.join(charts_dir, 'perfil_avancado_radar.png'))
plt.close()

print(f"Radar avançado salvo em: {os.path.join(charts_dir, 'perfil_avancado_radar.png')}")

# --- Radar de métricas avançadas de desempenho com tabela comparativa (melhorada e compacta) ---
fig = plt.figure(figsize=(15,7))
gs = fig.add_gridspec(1, 2, width_ratios=[2, 1.2])
ax = fig.add_subplot(gs[0], polar=True)

ax.plot(angles_adv, adv_norm_go, label='Go', linewidth=2, color='tab:blue')
ax.fill(angles_adv, adv_norm_go, alpha=0.15, color='tab:blue')
ax.plot(angles_adv, adv_norm_py, label='Python', linewidth=2, color='tab:orange')
ax.fill(angles_adv, adv_norm_py, alpha=0.15, color='tab:orange')

ax.set_thetagrids(np.degrees(angles_adv[:-1]), advanced_labels, fontsize=13)
ax.set_yticklabels([])
ax.set_title('Radar de métricas avançadas de desempenho', size=16, pad=22)
ax.legend(loc='upper right', bbox_to_anchor=(1.2, 1.1))

# Tabela comparativa melhorada e compacta, com coluna "Melhor"
ax_table = fig.add_subplot(gs[1])
ax_table.axis('off')
col_labels = ['Métrica', 'Go', 'Python', 'Melhor']
# Ajusta nomes para evitar corte na tabela
label_map = {
    'Eficiência Relativa': 'Eficiência\nRelativa',
    'Resp. por Mensagem': 'Resp.\npor Mensagem',
    'Consistência (DPR)': 'Consistência\n(DPR)',
}
# Unidades para cada métrica
metric_units = [
    '\n',           # Escalabilidade (adimensional)
    '\n',           # Eficiência Relativa (adimensional)
    '\n',           # Consistência (adimensional)
    '\nms/msg',     # Resp. por Mensagem
    '\n',           # Speedup (adimensional)
    '\nms/cli'      # Overhead
]
table_data = []
for i, label in enumerate(advanced_labels):
    label_show = label_map.get(label, label)
    go_val = adv_stats['Go'][i]
    py_val = adv_stats['Python'][i]
    unidade = metric_units[i]
    # Define qual linguagem foi melhor
    if label in ['Resp. por Mensagem', 'Overhead']:
        if go_val < py_val:
            melhor = 'Go'
        elif py_val < go_val:
            melhor = 'Python'
        else:
            melhor = 'Empate'
    else:
        if go_val > py_val:
            melhor = 'Go'
        elif py_val > go_val:
            melhor = 'Python'
        else:
            melhor = 'Empate'
    table_data.append([
        label_show,
        f'{go_val:.4f}{unidade}',
        f'{py_val:.4f}{unidade}',
        melhor
    ])

# Monta tabela com mais espaçamento, fonte maior e cabeçalho destacado
cell_colours = [['#e0e7ef']*4] + [['#f8fafc']*4 if i%2==0 else ['#e5e7eb']*4 for i in range(len(table_data))]
table = ax_table.table(cellText=[col_labels]+table_data, cellColours=cell_colours, cellLoc='center', loc='center')
table.auto_set_font_size(False)
table.set_fontsize(13)
table.scale(1.2, 1.5)

# Destaca cabeçalho
for j in range(4):
    table[(0, j)].set_text_props(weight='bold', color='#1e293b')
    table[(0, j)].set_height(0.15)

# Ajusta altura das linhas de dados
total_rows = len(table_data)+1
for i in range(1, total_rows):
    for j in range(4):
        table[(i, j)].set_height(0.11)

plt.tight_layout()
plt.savefig(os.path.join(charts_dir, 'perfil_avancado_radar.png'), dpi=300, bbox_inches='tight')
plt.close()
