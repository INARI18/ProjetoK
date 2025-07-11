import plotly.graph_objs as go
import plotly.io as pio

def plot_3d_surface_interactive_compare(data, charts_dir):
    """
    Gera um gráfico 3D interativo comparando Go (azul) e Python (amarelo) para cada valor de num_mensagens.
    """
    # Descobrir todos os valores de num_mensagens presentes em qualquer linguagem
    all_nmsgs = set()
    for df in data.values():
        all_nmsgs.update(df['num_mensagens'].unique())
    for nmsg in sorted(all_nmsgs):
        surfaces = []
        for lang, color in [('Go', 'Blues'), ('Python', 'YlOrBr')]:
            df = data.get(lang)
            if df is None:
                continue
            df_n = df[df['num_mensagens'] == nmsg]
            if df_n.empty:
                continue
            pivot = df_n.pivot_table(index='num_clientes', columns='num_servidores', values='throughput_media', aggfunc='mean')
            X = pivot.columns.values
            Y = pivot.index.values
            Z = pivot.values
            surfaces.append(go.Surface(
                z=Z, x=X, y=Y, colorscale=color, name=lang,
                showscale=False, opacity=0.85,
                hovertemplate=f"Linguagem: {lang}<br>Nº Servidores: %{{x}}<br>Nº Clientes: %{{y}}<br>Throughput: %{{z:.2f}} msgs/s<extra></extra>"
            ))
        if not surfaces:
            print(f"[AVISO] Sem dados para {nmsg} mensagens em nenhuma linguagem.")
            continue
        fig = go.Figure(data=surfaces)
        fig.update_layout(
            title=f'Throughput 3D Interativo - Go (azul) vs Python (amarelo) - {nmsg} mensagens',
            scene=dict(
                xaxis_title='Nº de Servidores',
                yaxis_title='Nº de Clientes',
                zaxis_title='Throughput médio (msgs/s)'
            ),
            autosize=True,
            margin=dict(l=20, r=20, b=40, t=60),
            legend=dict(title='Linguagem')
        )
        out_path = os.path.join(charts_dir, f'comparativo_3d_{nmsg}_interativo.html')
        pio.write_html(fig, file=out_path, auto_open=False)
        print(f"Gráfico 3D interativo salvo em {out_path}")

# --- Geração de gráficos 3D interativos a partir dos relatórios estatísticos ---
import os
import pandas as pd

base_dir = os.path.dirname(__file__)
reports_dir = os.path.join(base_dir, '..', 'results', 'reports')
charts_dir = os.path.join(base_dir, '..', 'results', 'charts')
os.makedirs(charts_dir, exist_ok=True)

files = {
    'Go': os.path.join(reports_dir, 'statistical_report_go.csv'),
    'Python': os.path.join(reports_dir, 'statistical_report_python.csv')
}

data = {}
for lang, path in files.items():
    if os.path.exists(path):
        df = pd.read_csv(path)
        data[lang] = df
    else:
        print(f"[AVISO] Relatório não encontrado para {lang}: {path}")

plot_3d_surface_interactive_compare(data, charts_dir)


