import plotly.graph_objs as go
import plotly.io as pio

def plot_3d_surface_interactive_compare(data, charts_dir):
    """
    Gera um gráfico 3D interativo com slider para cada linguagem, onde cada slide é um valor de num_mensagens.
    Salva um arquivo HTML por linguagem.
    """
    for lang, color in [('Go', 'Blues'), ('Python', 'YlOrBr')]:
        df = data.get(lang)
        if df is None:
            print(f"[AVISO] Relatório não encontrado para {lang}.")
            continue
        nmsgs = sorted(df['num_mensagens'].unique())
        frames = []
        slider_steps = []
        for i, nmsg in enumerate(nmsgs):
            df_n = df[df['num_mensagens'] == nmsg]
            if df_n.empty:
                continue
            pivot = df_n.pivot_table(index='num_clientes', columns='num_servidores', values='throughput_media', aggfunc='mean')
            X = pivot.columns.values
            Y = pivot.index.values
            Z = pivot.values
            surface = go.Surface(
                z=Z, x=X, y=Y, colorscale=color, name=lang,
                showscale=False, opacity=0.85,
                hovertemplate=f"Linguagem: {lang}<br>Nº Servidores: %{{x}}<br>Nº Clientes: %{{y}}<br>Throughput: %{{z:.2f}} msgs/s<extra></extra>"
            )
            frames.append(go.Frame(data=[surface], name=str(nmsg), traces=[0]))
            slider_steps.append({
                "args": [[str(nmsg)], {"frame": {"duration": 0, "redraw": True}, "mode": "immediate"}],
                "label": str(nmsg),
                "method": "animate"
            })
        if not frames:
            print(f"[AVISO] Sem dados para {lang}.")
            continue
        # Inicializa com o primeiro frame
        fig = go.Figure(
            data=[frames[0].data[0]],
            frames=frames
        )
        fig.update_layout(
            title=f'Throughput 3D Interativo - {lang} - Slider Nº Mensagens',
            scene=dict(
                xaxis_title='Nº de Servidores',
                yaxis_title='Nº de Clientes',
                zaxis_title='Throughput médio (msgs/s)'
            ),
            autosize=True,
            margin=dict(l=20, r=20, b=40, t=60),
            updatemenus=[{
                "type": "buttons",
                "buttons": [
                    {
                        "label": "Play",
                        "method": "animate",
                        "args": [None, {"frame": {"duration": 1000, "redraw": True}, "fromcurrent": True}]
                    },
                    {
                        "label": "Pause",
                        "method": "animate",
                        "args": [[None], {"frame": {"duration": 0, "redraw": False}, "mode": "immediate"}]
                    }
                ],
                "direction": "left",
                "pad": {"r": 10, "t": 87},
                "showactive": False,
                "x": 0.1,
                "xanchor": "right",
                "y": 0,
                "yanchor": "top"
            }],
            sliders=[{
                "active": 0,
                "yanchor": "top",
                "xanchor": "left",
                "currentvalue": {"font": {"size": 16}, "prefix": "Nº Mensagens: ", "visible": True, "xanchor": "right"},
                "transition": {"duration": 0, "easing": "cubic-in-out"},
                "pad": {"b": 10, "t": 50},
                "len": 0.9,
                "x": 0.1,
                "y": 0,
                "steps": slider_steps
            }]
        )
        out_path = os.path.join(charts_dir, f'slider_3d_{lang.lower()}.html')
        pio.write_html(fig, file=out_path, auto_open=False)
        print(f"Gráfico 3D interativo com slider salvo em {out_path}")

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
faltando = []
for lang, path in files.items():
    if os.path.exists(path):
        df = pd.read_csv(path)
        data[lang] = df
    else:
        print(f"[AVISO] Relatorio nao encontrado para {lang}: {path}")
        faltando.append(lang)

if len(data) < 2:
    print("[ERRO] Eh necessario ter os relatorios estatisticos de Go e Python para gerar graficos comparativos.")
    if faltando:
        print(f"Faltando: {', '.join(faltando)}")
    exit(1)

plot_3d_surface_interactive_compare(data, charts_dir)