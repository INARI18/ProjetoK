import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

def gerar_graficos_individuais_por_mensagem():
    """
    Gera gráficos individuais do tipo 'Tempo de Resposta vs Clientes' 
    para cada cenário de mensagens (1, 10, 100, 500, 1000, 10000)
    """
    try:
        df = pd.read_csv("../../resultados/csv/resultados_teste_carga.csv")
    except FileNotFoundError:
        print("Arquivo de resultados não encontrado!")
        return
    
    # Converter colunas numéricas e renomear Throughput para Taxa de Transferência
    df['Tempo Médio (s)'] = pd.to_numeric(df['Tempo Médio (s)'], errors='coerce')
    df['Taxa de Transferência (req/s)'] = pd.to_numeric(df['Throughput (req/s)'], errors='coerce')
    
    # Aplicar limpeza de outliers usando z-score
    df_clean = df.copy()
    for grupo_keys, grupo in df.groupby(['Servidores', 'Clientes', 'Mensagens', 'Linguagem']):
        if len(grupo) > 3:
            z_scores = np.abs((grupo['Tempo Médio (s)'] - grupo['Tempo Médio (s)'].mean()) / grupo['Tempo Médio (s)'].std())
            outliers = z_scores > 2.0
            if outliers.any():
                print(f"Removidos {outliers.sum()} outliers do grupo {grupo_keys}")
                df_clean = df_clean.drop(grupo[outliers].index)
    
    df = df_clean
    
    # Obter todas as quantidades de mensagens únicas
    quantidades_mensagens = sorted(df['Mensagens'].unique())
    
    # Cores consistentes para servidores
    colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd']
    
    print(f"Gerando {len(quantidades_mensagens)} gráficos individuais por cenário de mensagens...")
    
    # Gerar um arquivo PNG para cada quantidade de mensagens
    for mensagens in quantidades_mensagens:
        plt.figure(figsize=(12, 8))
        
        plt.title(f'Análise de Performance - {mensagens} Mensagem{"s" if mensagens > 1 else ""} por Cliente', 
                 fontsize=16, fontweight='bold', pad=20)
        
        # Filtrar dados para esta quantidade de mensagens
        df_mensagem = df[df["Mensagens"] == mensagens]
        
        if not df_mensagem.empty:
            # Plot para cada número de servidores
            for i, servidores in enumerate(sorted(df_mensagem["Servidores"].unique())):
                subset = df_mensagem[df_mensagem["Servidores"] == servidores]
                if not subset.empty:
                    # Agrupar por clientes e calcular média
                    grouped = subset.groupby("Clientes")["Tempo Médio (s)"].mean()
                    plt.plot(grouped.index, grouped.values, 
                           marker='o', linestyle='-', linewidth=3, markersize=8,
                           color=colors[i % len(colors)], 
                           label=f"{servidores} Servidor{'es' if servidores > 1 else ''}")
            
            plt.xlabel("Número de Clientes", fontsize=14)
            plt.ylabel("Tempo Médio de Resposta (segundos)", fontsize=14)
            plt.legend(loc='upper left', fontsize=12)
            plt.grid(True, alpha=0.3)
            plt.xlim(left=5)
            
            # Adicionar informações estatísticas no gráfico
            tempo_medio_geral = df_mensagem['Tempo Médio (s)'].mean()
            tempo_min = df_mensagem['Tempo Médio (s)'].min()
            tempo_max = df_mensagem['Tempo Médio (s)'].max()
            
            stats_text = f"""Estatísticas para {mensagens} mensagem{"s" if mensagens > 1 else ""}:
• Tempo médio geral: {tempo_medio_geral:.3f}s
• Melhor tempo: {tempo_min:.3f}s
• Pior tempo: {tempo_max:.3f}s
• Total de testes: {len(df_mensagem)}"""
            
            plt.text(0.02, 0.98, stats_text, transform=plt.gca().transAxes, 
                    fontsize=10, verticalalignment='top',
                    bbox=dict(boxstyle="round,pad=0.5", facecolor="lightblue", alpha=0.7))
        else:
            plt.text(0.5, 0.5, f'Dados para {mensagens} mensagem(s)\nnão disponíveis', 
                   ha='center', va='center', fontsize=14)
        
        # Salvar gráfico individual
        filename = f"../../resultados/graficos/analise_performance_{mensagens}_mensagens.png"
        plt.tight_layout()
        plt.savefig(filename, dpi=300, bbox_inches='tight')
        print(f"Gráfico salvo: {filename}")
        plt.close()  # Fechar para liberar memória

def gerar_graficos():
    # Carregar dados do CSV atualizado
    try:
        df = pd.read_csv("../../resultados/csv/resultados_teste_carga.csv")
    except FileNotFoundError:
        print("Arquivo de resultados não encontrado!")
        return
    
    # Converter colunas numéricas e renomear Throughput para Taxa de Transferência
    df['Tempo Médio (s)'] = pd.to_numeric(df['Tempo Médio (s)'], errors='coerce')
    df['Taxa de Transferência (req/s)'] = pd.to_numeric(df['Throughput (req/s)'], errors='coerce')
    
    # Aplicar limpeza de outliers usando z-score
    df_clean = df.copy()
    for grupo_keys, grupo in df.groupby(['Servidores', 'Clientes', 'Mensagens', 'Linguagem']):
        if len(grupo) > 3:  # Só aplica se tiver dados suficientes
            z_scores = np.abs((grupo['Tempo Médio (s)'] - grupo['Tempo Médio (s)'].mean()) / grupo['Tempo Médio (s)'].std())
            outliers = z_scores > 2.0
            if outliers.any():
                print(f"Removidos {outliers.sum()} outliers do grupo {grupo_keys}")
                df_clean = df_clean.drop(grupo[outliers].index)
    
    # Usar dados limpos para análise
    df = df_clean
    
    # Configurar estilo dos gráficos
    plt.style.use('default')
    plt.rcParams['figure.figsize'] = (15, 10)
    
    # Criar figura com 2 subplots principais
    fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(16, 12))
    fig.suptitle('Análise de Performance - Sistema Cliente-Servidor', fontsize=16, fontweight='bold')
    
    # 1. Gráfico de linhas focado: Apenas 100 mensagens (cenário mais pesado)
    ax1.set_title('Tempo de Resposta vs Clientes (100 mensagens)', fontweight='bold')
    
    # Filtrar apenas cenários com 100 mensagens para reduzir ruído visual
    df_100msg = df[df["Mensagens"] == 100]
    
    if not df_100msg.empty:
        # Cores mais distintas para cada número de servidores
        colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd']
        
        for i, servidores in enumerate(sorted(df_100msg["Servidores"].unique())):
            subset = df_100msg[df_100msg["Servidores"] == servidores]
            if not subset.empty:
                # Agrupar por clientes e calcular média
                grouped = subset.groupby("Clientes")["Tempo Médio (s)"].mean()
                ax1.plot(grouped.index, grouped.values, 
                        marker='o', linestyle='-', linewidth=2.5, markersize=6,
                        color=colors[i % len(colors)], 
                        label=f"{servidores} Servidor{'es' if servidores > 1 else ''}")
    
        ax1.set_xlabel("Número de Clientes")
        ax1.set_ylabel("Tempo Médio (s)")
        ax1.legend(loc='upper left', fontsize=10)
        ax1.grid(True, alpha=0.3)
        ax1.set_xlim(left=5)
    else:
        ax1.text(0.5, 0.5, 'Dados de 100 mensagens\nnão disponíveis', 
                transform=ax1.transAxes, ha='center', va='center', fontsize=12)
    
    # 2. Gráfico de barras: Taxa de Transferência máxima por configuração de servidores
    ax2.set_title('Taxa de Transferência Máxima por Número de Servidores', fontweight='bold')
    
    # Calcular Taxa de Transferência máxima por número de servidores
    throughput_max = df.groupby(['Servidores', 'Mensagens'])['Taxa de Transferência (req/s)'].max().unstack()
    
    # Posições das barras
    x = np.arange(len(throughput_max.index))
    width = 0.25
    
    # Criar barras para cada tipo de mensagem
    colors = ['#2E86AB', '#A23B72', '#F18F01']
    for i, (mensagens, color) in enumerate(zip([1, 10, 100], colors)):
        if mensagens in throughput_max.columns:
            values = throughput_max[mensagens].fillna(0)
            ax2.bar(x + i*width, values, width, label=f'{mensagens} mensagem(s)', 
                   color=color, alpha=0.8)
    
    ax2.set_xlabel('Número de Servidores')
    ax2.set_ylabel('Taxa de Transferência Máxima (req/s)')
    ax2.set_xticks(x + width)
    ax2.set_xticklabels(throughput_max.index)
    ax2.legend()
    ax2.grid(True, alpha=0.3, axis='y')
    
    # 3. Comparação de linguagens (se houver dados Go)
    ax3.set_title('Comparação de Performance: Python vs Go', fontweight='bold')
    
    if 'Linguagem' in df.columns and len(df['Linguagem'].unique()) > 1:
        lang_comparison = df.groupby(['Linguagem', 'Mensagens'])['Tempo Médio (s)'].mean().unstack()
        
        if not lang_comparison.empty:
            lang_comparison.plot(kind='bar', ax=ax3, color=['#4CAF50', '#FF9800', '#F44336'])
            ax3.set_xlabel('Linguagem')
            ax3.set_ylabel('Tempo Médio (s)')
            ax3.tick_params(axis='x', rotation=0)
            ax3.legend(title='Mensagens')
            ax3.grid(True, alpha=0.3, axis='y')
        else:
            ax3.text(0.5, 0.5, 'Dados de comparação\nnão disponíveis', 
                    transform=ax3.transAxes, ha='center', va='center', fontsize=12)
    else:
        ax3.text(0.5, 0.5, 'Apenas Python testado\n(Go não disponível)', 
                transform=ax3.transAxes, ha='center', va='center', fontsize=12)
    
    # 4. Resumo estatístico em texto
    ax4.axis('off')
    
    # Calcular estatísticas
    total_testes = len(df)
    tempo_medio_geral = df['Tempo Médio (s)'].mean()
    throughput_medio = df['Taxa de Transferência (req/s)'].mean()
    melhor_tempo = df['Tempo Médio (s)'].min()
    melhor_throughput = df['Taxa de Transferência (req/s)'].max()
    
    # Contar testes por linguagem
    if 'Linguagem' in df.columns:
        testes_python = len(df[df['Linguagem'] == 'Python'])
        testes_go = len(df[df['Linguagem'] == 'Go'])
        lang_info = f"Testes Python: {testes_python}\nTestes Go: {testes_go}"
    else:
        lang_info = "Linguagem: Python apenas"
    
    # Taxa de erro se houver coluna de erros
    if 'Erros' in df.columns:
        total_sucessos = df['Sucessos'].sum()
        total_erros = df['Erros'].sum()
        taxa_erro = (total_erros / (total_sucessos + total_erros)) * 100 if (total_sucessos + total_erros) > 0 else 0
        erro_info = f"Taxa de erro geral: {taxa_erro:.2f}%"
    else:
        erro_info = "Taxa de erro: N/D"
    
    stats_text = f"""RESUMO DA ANÁLISE

Total de testes executados: {total_testes}

PERFORMANCE:
• Tempo médio geral: {tempo_medio_geral:.3f}s
• Taxa de transferência média: {throughput_medio:.2f} req/s
• Melhor tempo: {melhor_tempo:.3f}s  
• Melhor taxa de transferência: {melhor_throughput:.2f} req/s

CONFIGURAÇÕES TESTADAS:
• Servidores: {sorted(df['Servidores'].unique())}
• Clientes: {min(df['Clientes'])} a {max(df['Clientes'])}
• Mensagens: {sorted(df['Mensagens'].unique())}

EXECUÇÃO:
{lang_info}
{erro_info}

GRÁFICOS:
• Superior esq.: Foco em 100 mensagens (cenário pesado)
• Superior dir.: Taxa de transferência máxima por configuração
• Inferior esq.: Comparação Python vs Go
• Inferior dir.: Este resumo estatístico"""
    
    ax4.text(0.05, 0.95, stats_text, transform=ax4.transAxes, fontsize=10, 
            verticalalignment='top', fontfamily='monospace',
            bbox=dict(boxstyle="round,pad=0.5", facecolor="lightgray", alpha=0.8))
    
    # Ajustar layout
    plt.tight_layout()
    plt.subplots_adjust(top=0.93)  # Espaço para o título principal
    
    # Salvar gráfico
    plt.savefig('../../resultados/graficos/analise_performance.png', dpi=300, bbox_inches='tight')
    print("Gráfico salvo: ../../resultados/graficos/analise_performance.png")
    plt.show()
    
    # Gerar relatórios essenciais
    gerar_relatorio_simples(df)

def gerar_relatorio_simples(df):
    """Gera relatórios CSV essenciais com estatísticas avançadas (média de 10 execuções)"""
    
    # Agrupar por configuração e calcular estatísticas de 10 execuções
    summary_data = []
    
    for (servidores, clientes, mensagens, linguagem), group in df.groupby(['Servidores', 'Clientes', 'Mensagens', 'Linguagem']):
        if len(group) >= 5:  # Só processa se tiver dados suficientes
            # Remover outliers usando z-score manual (sem scipy)
            tempo_mean = group['Tempo Médio (s)'].mean()
            tempo_std = group['Tempo Médio (s)'].std()
            if tempo_std > 0:
                z_scores = abs((group['Tempo Médio (s)'] - tempo_mean) / tempo_std)
                group_clean = group[z_scores < 2.0]  # Remove outliers > 2 desvios
            else:
                group_clean = group
            
            # Calcular estatísticas avançadas
            stats = {
                'Servidores': servidores,
                'Clientes': clientes, 
                'Mensagens': mensagens,
                'Linguagem': linguagem,
                'Tempo_Medio_s': round(group_clean['Tempo Médio (s)'].mean(), 3),
                'Tempo_Mediana_s': round(group_clean['Tempo Médio (s)'].median(), 3),
                'Tempo_StdDev_s': round(group_clean['Tempo Médio (s)'].std(), 3),
                'Tempo_Min_s': round(group_clean['Tempo Médio (s)'].min(), 3),
                'Tempo_Max_s': round(group_clean['Tempo Médio (s)'].max(), 3),
                'Taxa_Transferencia_Media_req_s': round(group_clean['Taxa de Transferência (req/s)'].mean(), 2),
                'Taxa_Transferencia_Mediana_req_s': round(group_clean['Taxa de Transferência (req/s)'].median(), 2),
                'Taxa_Transferencia_StdDev_req_s': round(group_clean['Taxa de Transferência (req/s)'].std(), 2),
                'Taxa_Transferencia_Min_req_s': round(group_clean['Taxa de Transferência (req/s)'].min(), 2),
                'Taxa_Transferencia_Max_req_s': round(group_clean['Taxa de Transferência (req/s)'].max(), 2),
                'Total_Sucessos': int(group_clean['Sucessos'].sum()),
                'Total_Erros': int(group_clean['Erros'].sum()),
                'Num_Execucoes': len(group_clean),
                'Outliers_Removidos': len(group) - len(group_clean),
                'Taxa_Sucesso_Percent': round((group_clean['Sucessos'].sum() / (group_clean['Sucessos'].sum() + group_clean['Erros'].sum())) * 100, 2) if (group_clean['Sucessos'].sum() + group_clean['Erros'].sum()) > 0 else 0
            }
            summary_data.append(stats)
    
    # Salvar estatísticas detalhadas
    if summary_data:
        summary_df = pd.DataFrame(summary_data)
        summary_df.to_csv('../../resultados/relatorios/estatisticas_avancadas.csv', index=False)
        print("Estatísticas avançadas salvas: ../../resultados/relatorios/estatisticas_avancadas.csv")
    
    # Comparação de linguagens (se aplicável)
    if 'Linguagem' in df.columns and len(df['Linguagem'].unique()) > 1:
        lang_data = []
        
        for linguagem, group in df.groupby('Linguagem'):
            lang_stats = {
                'Linguagem': linguagem,
                'Tempo_Medio_s': round(group['Tempo Médio (s)'].mean(), 3),
                'Tempo_StdDev_s': round(group['Tempo Médio (s)'].std(), 3),
                'Tempo_Min_s': round(group['Tempo Médio (s)'].min(), 3),
                'Tempo_Max_s': round(group['Tempo Médio (s)'].max(), 3),
                'Taxa_Transferencia_Media_req_s': round(group['Taxa de Transferência (req/s)'].mean(), 2),
                'Taxa_Transferencia_StdDev_req_s': round(group['Taxa de Transferência (req/s)'].std(), 2),
                'Taxa_Transferencia_Min_req_s': round(group['Taxa de Transferência (req/s)'].min(), 2),
                'Taxa_Transferencia_Max_req_s': round(group['Taxa de Transferência (req/s)'].max(), 2),
                'Total_Sucessos': int(group['Sucessos'].sum()),
                'Total_Erros': int(group['Erros'].sum()),
                'Num_Testes': len(group),
                'Taxa_Sucesso_Percent': round((group['Sucessos'].sum() / (group['Sucessos'].sum() + group['Erros'].sum())) * 100, 2) if (group['Sucessos'].sum() + group['Erros'].sum()) > 0 else 0
            }
            lang_data.append(lang_stats)
        
        lang_df = pd.DataFrame(lang_data)
        lang_df.to_csv('../../resultados/csv/comparacao_linguagens.csv', index=False)
        print("Comparação de linguagens salva: ../../resultados/csv/comparacao_linguagens.csv")
    
    # Resumo executivo mais detalhado
    # Encontrar configurações ótimas
    melhor_tempo_idx = df['Tempo Médio (s)'].idxmin()
    melhor_throughput_idx = df['Taxa de Transferência (req/s)'].idxmax()
    
    resumo_executivo = {
        'Metrica': [
            'Total_de_Testes_Executados',
            'Tempo_Medio_Geral_s',
            'Taxa_Transferencia_Media_Geral_req_s', 
            'Melhor_Tempo_s',
            'Melhor_Taxa_Transferencia_req_s',
            'Config_Melhor_Tempo_Servidores',
            'Config_Melhor_Tempo_Clientes',
            'Config_Melhor_Tempo_Mensagens',
            'Config_Melhor_Tempo_Linguagem',
            'Config_Melhor_Taxa_Transferencia_Servidores',
            'Config_Melhor_Taxa_Transferencia_Clientes', 
            'Config_Melhor_Taxa_Transferencia_Mensagens',
            'Config_Melhor_Taxa_Transferencia_Linguagem',
            'Taxa_Erro_Geral_Percent',
            'Total_Sucessos',
            'Total_Erros'
        ],
        'Valor': [
            len(df),
            round(df['Tempo Médio (s)'].mean(), 3),
            round(df['Taxa de Transferência (req/s)'].mean(), 2),
            round(df['Tempo Médio (s)'].min(), 3),
            round(df['Taxa de Transferência (req/s)'].max(), 2),
            df.loc[melhor_tempo_idx, 'Servidores'],
            df.loc[melhor_tempo_idx, 'Clientes'],
            df.loc[melhor_tempo_idx, 'Mensagens'],
            df.loc[melhor_tempo_idx, 'Linguagem'] if 'Linguagem' in df.columns else 'N/A',
            df.loc[melhor_throughput_idx, 'Servidores'],
            df.loc[melhor_throughput_idx, 'Clientes'],
            df.loc[melhor_throughput_idx, 'Mensagens'],
            df.loc[melhor_throughput_idx, 'Linguagem'] if 'Linguagem' in df.columns else 'N/A',
            round((df['Erros'].sum() / (df['Sucessos'].sum() + df['Erros'].sum())) * 100, 2) if (df['Sucessos'].sum() + df['Erros'].sum()) > 0 else 0,
            df['Sucessos'].sum(),
            df['Erros'].sum()
        ]
    }
    
    resumo_df = pd.DataFrame(resumo_executivo)
    resumo_df.to_csv('../../resultados/relatorios/resumo_executivo.csv', index=False)
    print("Resumo executivo salvo: ../../resultados/relatorios/resumo_executivo.csv")

if __name__ == "__main__":
    # Gerar gráficos individuais por cenário de mensagens
    gerar_graficos_individuais_por_mensagem()
    
    # Gerar gráfico consolidado
    gerar_graficos()
