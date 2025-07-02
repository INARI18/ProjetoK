#!/usr/bin/env python3
"""
Gerar Gráficos - ProjetoK
Script unificado para geração de relatório visual.
Gera APENAS o relatório final com métricas comparativas de Go vs Python.
"""

import json
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
from pathlib import Path
import glob
from datetime import datetime
import time

# Configuração do matplotlib para melhor aparência
plt.style.use('seaborn-v0_8')
plt.rcParams['figure.figsize'] = (20, 12)
plt.rcParams['font.size'] = 11

# Obter caminho absoluto da raiz do projeto
SCRIPT_DIR = Path(__file__).parent.absolute()
PROJECT_ROOT = SCRIPT_DIR.parent.parent  # src/testes -> src -> ProjetoK
RESULTADOS_DIR = PROJECT_ROOT / "resultados"
GRAFICOS_DIR = RESULTADOS_DIR / "graficos"
RELATORIOS_DIR = RESULTADOS_DIR / "relatorios"

class GeradorGraficos:
    def __init__(self):
        # Criar diretórios se não existirem
        RESULTADOS_DIR.mkdir(exist_ok=True)
        GRAFICOS_DIR.mkdir(exist_ok=True)
        RELATORIOS_DIR.mkdir(exist_ok=True)
        
        self.df_dados = None  # DataFrame principal com todos os dados
        
        print(f"📁 Diretório de resultados: {RESULTADOS_DIR}")
        print(f"📁 Diretório de gráficos: {GRAFICOS_DIR}")
        print(f"📁 Diretório de relatórios: {RELATORIOS_DIR}")
        
        self._carregar_dados_csv()
    
    def _carregar_dados_csv(self):
        """Carregar dados do relatório estatístico CSV"""
        print("📂 Carregando dados do relatório estatístico...")
        
        csv_file = RELATORIOS_DIR / "relatorio_estatistico.csv"
        
        if csv_file.exists():
            try:
                self.df_dados = pd.read_csv(csv_file, encoding='utf-8')
                print(f"✅ Carregado: {csv_file.name}")
                print(f"📊 Total de execuções: {len(self.df_dados)}")
                
                # Exibir resumo por linguagem
                if 'linguagem' in self.df_dados.columns:
                    resumo = self.df_dados['linguagem'].value_counts()
                    for linguagem, count in resumo.items():
                        print(f"   📊 {linguagem}: {count} execuções")
                
                # Verificar e remover outliers automaticamente
                self._processar_outliers()
                
            except Exception as e:
                print(f"❌ Erro ao carregar CSV: {e}")
                print("⚠️  Tentando carregar dados dos JSONs como fallback...")
                self._carregar_dados_json_fallback()
        else:
            print("⚠️  Arquivo relatorio_estatistico.csv não encontrado")
            print("📝 Gerando relatório estatístico primeiro...")
            self._carregar_dados_json_fallback()
            if self.df_dados is not None:
                self._salvar_csv()
    
    def _processar_outliers(self):
        """Identificar e opcionalmente remover outliers dos dados"""
        if self.df_dados is None or len(self.df_dados) == 0:
            return
        
        print("🧹 Analisando outliers...")
        
        # Identificar outliers por métrica usando IQR
        metricas = ['throughput', 'latencia_media', 'tempo_execucao']
        outliers_total = set()
        
        for metrica in metricas:
            if metrica in self.df_dados.columns:
                # Calcular outliers por linguagem separadamente
                for linguagem in self.df_dados['linguagem'].unique():
                    dados_linguagem = self.df_dados[self.df_dados['linguagem'] == linguagem]
                    
                    Q1 = dados_linguagem[metrica].quantile(0.25)
                    Q3 = dados_linguagem[metrica].quantile(0.75)
                    IQR = Q3 - Q1
                    
                    # Outliers moderados (1.5 * IQR)
                    limite_inferior = Q1 - 1.5 * IQR
                    limite_superior = Q3 + 1.5 * IQR
                    
                    outliers_metrica = dados_linguagem[
                        (dados_linguagem[metrica] < limite_inferior) | 
                        (dados_linguagem[metrica] > limite_superior)
                    ].index
                    
                    outliers_total.update(outliers_metrica)
                    
                    if len(outliers_metrica) > 0:
                        print(f"   📊 {linguagem} - {metrica}: {len(outliers_metrica)} outliers identificados")
        
        if outliers_total:
            print(f"🔍 Total de outliers encontrados: {len(outliers_total)} de {len(self.df_dados)} registros")
            print(f"📊 Percentual de outliers: {len(outliers_total)/len(self.df_dados)*100:.1f}%")
            
            # Remover outliers apenas se forem menos de 10% dos dados
            if len(outliers_total) / len(self.df_dados) < 0.10:
                self.df_dados = self.df_dados.drop(index=outliers_total)
                print(f"✅ Outliers removidos. Dados restantes: {len(self.df_dados)}")
            else:
                print("⚠️  Muitos outliers encontrados (>10%). Mantendo todos os dados.")
        else:
            print("✅ Nenhum outlier significativo encontrado")
    
    def _carregar_dados_json_fallback(self):
        """Carregar dados dos JSONs como fallback"""
        print("📂 Carregando dados dos arquivos JSON...")
        
        dados_go = []
        dados_python = []
        
        # Procurar arquivos de resultados Go
        arquivos_go = glob.glob(str(RELATORIOS_DIR / "resultados_go*.json"))
        for arquivo in arquivos_go:
            try:
                with open(arquivo, 'r', encoding='utf-8') as f:
                    dados = json.load(f)
                    if 'resultados' in dados:
                        dados_go.extend(dados['resultados'])
                    elif isinstance(dados, list):
                        dados_go.extend(dados)
                print(f"✅ Carregado: {Path(arquivo).name}")
            except Exception as e:
                print(f"❌ Erro ao carregar {arquivo}: {e}")
        
        # Procurar arquivos de resultados Python
        arquivos_python = glob.glob(str(RELATORIOS_DIR / "resultados_python*.json"))
        for arquivo in arquivos_python:
            try:
                with open(arquivo, 'r', encoding='utf-8') as f:
                    dados = json.load(f)
                    if 'resultados' in dados:
                        dados_python.extend(dados['resultados'])
                    elif isinstance(dados, list):
                        dados_python.extend(dados)
                print(f"✅ Carregado: {Path(arquivo).name}")
            except Exception as e:
                print(f"❌ Erro ao carregar {arquivo}: {e}")
        
        # Converter para DataFrame consolidado
        dados_consolidados = []
        
        for dado in dados_go:
            dados_consolidados.append({
                'linguagem': 'Go',
                'timestamp': dado.get('timestamp', ''),
                'ambiente': dado.get('ambiente', 'kubernetes'),
                'num_servidores': dado.get('num_servidores', 0),
                'num_clientes': dado.get('num_clientes', 0),
                'num_mensagens': dado.get('num_mensagens', 0),
                'repeticao': dado.get('repeticao', 0),
                'tempo_execucao': dado.get('tempo_execucao', 0),
                'total_mensagens': dado.get('total_mensagens', 0),
                'throughput': dado.get('throughput', 0),
                'latencia_media': dado.get('latencia_media', 0)
            })
        
        for dado in dados_python:
            dados_consolidados.append({
                'linguagem': 'Python',
                'timestamp': dado.get('timestamp', ''),
                'ambiente': dado.get('ambiente', 'kubernetes'),
                'num_servidores': dado.get('num_servidores', 0),
                'num_clientes': dado.get('num_clientes', 0),
                'num_mensagens': dado.get('num_mensagens', 0),
                'repeticao': dado.get('repeticao', 0),
                'tempo_execucao': dado.get('tempo_execucao', 0),
                'total_mensagens': dado.get('total_mensagens', 0),
                'throughput': dado.get('throughput', 0),
                'latencia_media': dado.get('latencia_media', 0)
            })
        
        if dados_consolidados:
            self.df_dados = pd.DataFrame(dados_consolidados)
            print(f"📊 Total de execuções carregadas: {len(self.df_dados)}")
        else:
            print("❌ Nenhum dado encontrado")
    
    def _salvar_csv(self):
        """Salvar dados consolidados em CSV"""
        if self.df_dados is not None and len(self.df_dados) > 0:
            csv_file = RELATORIOS_DIR / "relatorio_estatistico.csv"
            self.df_dados.to_csv(csv_file, index=False, encoding='utf-8')
            print(f"✅ Relatório CSV salvo: {csv_file}")
    
    def _filtrar_dados(self, linguagem=None):
        """Filtrar dados por linguagem"""
        if self.df_dados is None:
            return pd.DataFrame()
        
        if linguagem:
            return self.df_dados[self.df_dados['linguagem'] == linguagem].copy()
        else:
            return self.df_dados.copy()
    

    
    # Função única para gerar relatório final completo (gráfico de barras + 2 áreas empilhadas)
    
    def gerar_relatorio_final_completo(self):
        """Gráfico Final: Barras + Área Empilhada em um único PNG com proporções otimizadas"""
        if self.df_dados is None or len(self.df_dados) == 0:
            print("⚠️  Nenhum dado disponível para gerar relatório final")
            return
            
        df_go = self._filtrar_dados('Go')
        df_python = self._filtrar_dados('Python')
        
        if len(df_go) == 0 or len(df_python) == 0:
            print("⚠️  Dados insuficientes para relatório final")
            return
        
        # Criar figura com proporções otimizadas
        fig = plt.figure(figsize=(20, 12))
        
        # Layout melhorado: 3 linhas
        # Linha 1: Gráfico de barras (40% da altura)
        # Linhas 2-3: Área empilhada (60% da altura)
        
        ax_barras = plt.subplot2grid((5, 2), (0, 0), colspan=2, rowspan=2)  # 2/5 = 40%
        ax_go = plt.subplot2grid((5, 2), (2, 0), rowspan=3)                 # 3/5 = 60%
        ax_python = plt.subplot2grid((5, 2), (2, 1), rowspan=3)             # 3/5 = 60%
        
        # ========== GRÁFICO DE BARRAS (TOPO) ==========
        try:
            # Calcular métricas agregadas
            metricas_go = {
                'Throughput\nMédio': df_go['throughput'].mean(),
                'Throughput\nMáximo': df_go['throughput'].max(),
                'Latência\nMédia': df_go['latencia_media'].mean(),
                'Tempo\nExecução': df_go['tempo_execucao'].mean(),
                'Eficiência\n(msg/s/serv)': (df_go['throughput'] / df_go['num_servidores']).mean()
            }
            
            metricas_python = {
                'Throughput\nMédio': df_python['throughput'].mean(),
                'Throughput\nMáximo': df_python['throughput'].max(),
                'Latência\nMédia': df_python['latencia_media'].mean(),
                'Tempo\nExecução': df_python['tempo_execucao'].mean(),
                'Eficiência\n(msg/s/serv)': (df_python['throughput'] / df_python['num_servidores']).mean()
            }
            
            x = np.arange(len(metricas_go))
            width = 0.35
            
            valores_go = list(metricas_go.values())
            valores_python = list(metricas_python.values())
            labels = list(metricas_go.keys())
            
            # Normalizar latência e tempo
            valores_go_norm = valores_go.copy()
            valores_python_norm = valores_python.copy()
            
            valores_go_norm[2] = 1000 / valores_go[2] if valores_go[2] > 0 else 0
            valores_python_norm[2] = 1000 / valores_python[2] if valores_python[2] > 0 else 0
            valores_go_norm[3] = 100 / valores_go[3] if valores_go[3] > 0 else 0
            valores_python_norm[3] = 100 / valores_python[3] if valores_python[3] > 0 else 0
            
            labels[2] = 'Velocidade\n(1/latência)'
            labels[3] = 'Velocidade\n(1/tempo)'
            
            # Cores atualizadas: Go azul escuro, Python amarelo
            bars1 = ax_barras.bar(x - width/2, valores_go_norm, width, label='Go', 
                                 color='#1f4e79', alpha=0.9, edgecolor='black', linewidth=0.8)
            bars2 = ax_barras.bar(x + width/2, valores_python_norm, width, label='Python', 
                                 color='#ffcc00', alpha=0.9, edgecolor='black', linewidth=0.8)
            
            # Adicionar valores nas barras
            for i, (bar1, bar2) in enumerate(zip(bars1, bars2)):
                height1 = bar1.get_height()
                height2 = bar2.get_height()
                
                if i == 2:  # Latência
                    ax_barras.text(bar1.get_x() + bar1.get_width()/2., height1,
                                  f'{valores_go[i]:.1f}ms', ha='center', va='bottom', fontsize=10, fontweight='bold')
                    ax_barras.text(bar2.get_x() + bar2.get_width()/2., height2,
                                  f'{valores_python[i]:.1f}ms', ha='center', va='bottom', fontsize=10, fontweight='bold')
                elif i == 3:  # Tempo
                    ax_barras.text(bar1.get_x() + bar1.get_width()/2., height1,
                                  f'{valores_go[i]:.1f}s', ha='center', va='bottom', fontsize=10, fontweight='bold')
                    ax_barras.text(bar2.get_x() + bar2.get_width()/2., height2,
                                  f'{valores_python[i]:.1f}s', ha='center', va='bottom', fontsize=10, fontweight='bold')
                else:
                    ax_barras.text(bar1.get_x() + bar1.get_width()/2., height1,
                                  f'{valores_go[i]:,.0f}', ha='center', va='bottom', fontsize=10, fontweight='bold')
                    ax_barras.text(bar2.get_x() + bar2.get_width()/2., height2,
                                  f'{valores_python[i]:,.0f}', ha='center', va='bottom', fontsize=10, fontweight='bold')
            
            ax_barras.set_ylabel('Valores (normalizados)', fontweight='bold', fontsize=12)
            ax_barras.set_title('Comparativo Go vs Python - Métricas de Performance', 
                               fontsize=16, fontweight='bold', pad=20)
            ax_barras.set_xticks(x)
            ax_barras.set_xticklabels(labels, fontsize=11, ha='center')
            ax_barras.legend(loc='upper right', fontsize=12, frameon=True, fancybox=True, shadow=True)
            ax_barras.grid(True, alpha=0.3, axis='y')
            
            # Vencedor com destaque verde
            score_go = sum(valores_go_norm)
            score_python = sum(valores_python_norm)
            vencedor = "Go" if score_go > score_python else "Python"
            ratio = max(score_go, score_python) / min(score_go, score_python)
            
            ax_barras.text(0.02, 0.95, f'Vencedor: {vencedor} ({ratio:.1f}x melhor)', 
                          transform=ax_barras.transAxes, fontsize=14, fontweight='bold',
                          bbox=dict(boxstyle="round,pad=0.4", facecolor='#2e8b57', alpha=0.9, edgecolor='black'),
                          verticalalignment='top', color='white')
            
        except Exception as e:
            ax_barras.text(0.5, 0.5, f'Erro no gráfico de barras:\n{str(e)}', 
                          ha='center', va='center', transform=ax_barras.transAxes, fontsize=12)
        
        # ========== GRÁFICOS DE ÁREA EMPILHADA ==========
        
        def criar_area_empilhada_otimizada(df, ax, titulo, cores):
            try:
                pivot = df.groupby(['num_mensagens', 'num_servidores'])['throughput'].mean().unstack(fill_value=0)
                
                x = list(pivot.index)
                x_labels = [f'{int(val):,}' for val in x]
                
                areas_data = []
                labels_servidores = []
                
                for col in pivot.columns:
                    areas_data.append(pivot[col].values)
                    labels_servidores.append(f'{col} servidor{"es" if col > 1 else ""}')
                
                # Área empilhada com bordas
                polys = ax.stackplot(range(len(x)), *areas_data, 
                                   labels=labels_servidores,
                                   colors=cores, alpha=0.85, edgecolor='white', linewidth=0.5)
                
                # Linha total mais destacada
                total = pivot.sum(axis=1).values
                ax.plot(range(len(x)), total, 'k-', linewidth=3, alpha=0.9, 
                       label='Total', marker='o', markersize=6, markerfacecolor='white', 
                       markeredgecolor='black', markeredgewidth=2)
                
                ax.set_title(titulo, fontweight='bold', fontsize=14, pad=15)
                ax.set_xlabel('Número de Mensagens', fontsize=12, fontweight='bold')
                ax.set_ylabel('Throughput (msg/s)', fontsize=12, fontweight='bold')
                
                ax.set_xticks(range(len(x)))
                ax.set_xticklabels(x_labels, rotation=45, fontsize=10)
                
                # Valores no topo mais seletivos
                step = max(1, len(total) // 4)
                for i in range(0, len(total), step):
                    if total[i] > 0:
                        ax.text(i, total[i] + max(total)*0.03, f'{int(total[i]):,}', 
                               ha='center', va='bottom', fontweight='bold', fontsize=11,
                               bbox=dict(boxstyle="round,pad=0.2", facecolor='white', alpha=0.8))
                
                ax.legend(loc='upper left', fontsize=10, frameon=True, fancybox=True, shadow=True)
                ax.grid(True, alpha=0.3, axis='y')
                
                # Stats com destaque
                throughput_max = max(total)
                throughput_medio = np.mean(total)
                
                stats_text = f'Máximo: {int(throughput_max):,}\nMédia: {int(throughput_medio):,}'
                ax.text(0.98, 0.98, stats_text, transform=ax.transAxes, 
                       fontsize=11, fontweight='bold', verticalalignment='top', horizontalalignment='right',
                       bbox=dict(boxstyle="round,pad=0.3", facecolor='#f8f9fa', alpha=0.95, edgecolor='black'))
                
            except Exception as e:
                ax.text(0.5, 0.5, f'Erro:\n{str(e)}', ha='center', va='center', 
                       transform=ax.transAxes, fontsize=12)
        
        # Cores otimizadas
        cores_go = ['#0a1628', '#1f4e79', '#2e6da4', '#4a90e2', '#87ceeb']
        cores_python = ['#996633', '#cc8800', '#ffcc00', '#ffd700', '#fff8dc']
        
        # Área empilhada Go
        criar_area_empilhada_otimizada(df_go, ax_go, 'Go - Throughput Acumulado por Configuração', cores_go)
        
        # Área empilhada Python
        criar_area_empilhada_otimizada(df_python, ax_python, 'Python - Throughput Acumulado por Configuração', cores_python)
        
        # ========== LEGENDA GERAL OTIMIZADA ==========
        
        # Código para estatísticas (removido da exibição)
        total_execucoes = len(self.df_dados)
        execucoes_go = len(df_go)
        execucoes_python = len(df_python)
        throughput_max_go = df_go['throughput'].max()
        throughput_max_python = df_python['throughput'].max()
        ratio_performance = throughput_max_go / throughput_max_python if throughput_max_python > 0 else 0
        
        # Sem legenda inferior global
        
        # Ajustar layout com proporções otimizadas para evitar sobreposição
        plt.tight_layout()
        plt.subplots_adjust(top=0.95, bottom=0.12, left=0.08, right=0.96, 
                           hspace=0.8, wspace=0.2)
        
        arquivo_salvo = GRAFICOS_DIR / 'relatorio_final_completo.png'
        plt.savefig(arquivo_salvo, dpi=300, bbox_inches='tight',
                   facecolor='white', edgecolor='none')
        print(f"✅ Relatório Final salvo: {arquivo_salvo.name}")
        plt.close()
        
        return arquivo_salvo

    def gerar_relatorio_resumo(self):
        """Gera um relatório resumido em formato de texto"""
        if self.df_dados is None or len(self.df_dados) == 0:
            print("⚠️  Nenhum dado disponível para gerar relatório resumo")
            return
            
        df_go = self._filtrar_dados('Go')
        df_python = self._filtrar_dados('Python')
        
        if len(df_go) == 0 or len(df_python) == 0:
            print("⚠️  Dados insuficientes para relatório resumo")
            return
        
        # Calcular estatísticas
        data_atual = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
        
        # Estatísticas Go
        total_execucoes_go = len(df_go)
        throughput_medio_go = df_go['throughput'].mean()
        throughput_max_go = df_go['throughput'].max()
        throughput_min_go = df_go['throughput'].min()
        latencia_media_go = df_go['latencia_media'].mean()
        latencia_max_go = df_go['latencia_media'].max()
        latencia_min_go = df_go['latencia_media'].min()
        
        # Estatísticas Python
        total_execucoes_python = len(df_python)
        throughput_medio_python = df_python['throughput'].mean()
        throughput_max_python = df_python['throughput'].max()
        throughput_min_python = df_python['throughput'].min()
        latencia_media_python = df_python['latencia_media'].mean()
        latencia_max_python = df_python['latencia_media'].max()
        latencia_min_python = df_python['latencia_media'].min()
        
        # Comparativo
        diff_throughput = (throughput_medio_go / throughput_medio_python) * 100 - 100
        diff_latencia = (latencia_media_python / latencia_media_go) * 100 - 100
        
        # Gerar conteúdo do relatório
        conteudo = f"""================================================================================
RESUMO EXECUTIVO - PROJETO K
================================================================================
Data de geração: {data_atual}

LINGUAGEM GO
----------------------------------------
Total de execuções: {total_execucoes_go}
Throughput médio: {throughput_medio_go:.2f} msg/s
Throughput máximo: {throughput_max_go:.2f} msg/s
Throughput mínimo: {throughput_min_go:.2f} msg/s
Latência média: {latencia_media_go:.2f} ms
Latência máxima: {latencia_max_go:.2f} ms
Latência mínima: {latencia_min_go:.2f} ms

LINGUAGEM PYTHON
----------------------------------------
Total de execuções: {total_execucoes_python}
Throughput médio: {throughput_medio_python:.2f} msg/s
Throughput máximo: {throughput_max_python:.2f} msg/s
Throughput mínimo: {throughput_min_python:.2f} msg/s
Latência média: {latencia_media_python:.2f} ms
Latência máxima: {latencia_max_python:.2f} ms
Latência mínima: {latencia_min_python:.2f} ms

COMPARATIVO
----------------------------------------
Diferença de throughput (Go vs Python): {diff_throughput:.2f}%
Diferença de latência (Python vs Go): {diff_latencia:.2f}%"""
        
        # Salvar arquivo
        arquivo_resumo = RELATORIOS_DIR / "relatorio_resumo.txt"
        with open(arquivo_resumo, 'w', encoding='utf-8') as f:
            f.write(conteudo)
        
        print(f"✅ Relatório resumo salvo: {arquivo_resumo}")
        return arquivo_resumo


def main():
    """Função principal"""
    # Mostrar quanto tempo durou o processamento
    start_time = time.time()
    
    try:
        print("🎨 Iniciando geração do relatório final...")
        
        gerador = GeradorGraficos()  # Dados já são carregados no __init__
        
        print("\n🎯 Gerando Relatório Final Completo...")
        gerador.gerar_relatorio_final_completo()
        
        print("\n🎯 Gerando Relatório Resumo...")
        gerador.gerar_relatorio_resumo()
        
        print("\n" + "="*60)
        print(f"✅ Relatórios gerados com sucesso! ({time.time() - start_time:.1f} segundos)")
        print(f"📁 Gráficos salvos em: {GRAFICOS_DIR}")
        print(f"📁 Relatórios salvos em: {RELATORIOS_DIR}")
        print("\n🎯 ARQUIVOS GERADOS:")
        print("   📋 relatorio_final_completo.png (gráfico)")
        print("   📋 relatorio_resumo.txt (texto)")
        print("\n💡 Use estes arquivos para apresentações e relatórios!")
        print("="*60)
        
    except Exception as e:
        print(f"❌ Erro durante execução: {e}")
        print(f"⏱️ Tempo decorrido antes do erro: {time.time() - start_time:.1f} segundos")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
