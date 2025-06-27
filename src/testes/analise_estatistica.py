import pandas as pd
import numpy as np
import csv
import os
from scipy import stats
import warnings
warnings.filterwarnings('ignore')

def calcular_estatisticas_avancadas():
    """
    Gera estatísticas avançadas conforme requisitos:
    - máximo, mínimo, média, mediana, desvio padrão
    - Aplicação de z-score para remoção de outliers
    - Análise por configuração de teste
    """
    
    try:
        # Carregar dados brutos
        df = pd.read_csv("../../resultados/csv/resultados_teste_carga.csv")
        print(f"Carregados {len(df)} registros para análise estatística")
        
        # Verificar se temos as colunas necessárias
        colunas_necessarias = ['Servidores', 'Clientes', 'Mensagens', 'Linguagem', 'Tempo Médio (s)', 'Throughput (req/s)']
        if not all(col in df.columns for col in colunas_necessarias):
            print("ERRO: Colunas necessárias não encontradas no CSV")
            return False
            
        # Converter para numérico
        df['Tempo Médio (s)'] = pd.to_numeric(df['Tempo Médio (s)'], errors='coerce')
        df['Throughput (req/s)'] = pd.to_numeric(df['Throughput (req/s)'], errors='coerce')
        
        # Remover registros com valores inválidos
        df = df.dropna(subset=['Tempo Médio (s)', 'Throughput (req/s)'])
        
        if len(df) == 0:
            print("ERRO: Nenhum dado válido após limpeza")
            return False
            
        # Agrupar por configuração de teste
        grupos = ['Servidores', 'Clientes', 'Mensagens', 'Linguagem']
        
        # Análise estatística completa
        resultados_estatisticos = []
        outliers_removidos = 0
        
        for grupo_keys, grupo_data in df.groupby(grupos):
            servidores, clientes, mensagens, linguagem = grupo_keys
            
            if len(grupo_data) < 3:  # Precisa de pelo menos 3 amostras
                continue
                
            # Aplicar z-score para identificar outliers
            tempo_values = grupo_data['Tempo Médio (s)'].values
            throughput_values = grupo_data['Throughput (req/s)'].values
            
            # Z-score para tempo de resposta
            tempo_mean = np.mean(tempo_values)
            tempo_std = np.std(tempo_values)
            
            if tempo_std > 0:
                z_scores_tempo = np.abs((tempo_values - tempo_mean) / tempo_std)
                outliers_tempo = z_scores_tempo > 2.0
            else:
                outliers_tempo = np.zeros(len(tempo_values), dtype=bool)
            
            # Z-score para throughput
            throughput_mean = np.mean(throughput_values)
            throughput_std = np.std(throughput_values)
            
            if throughput_std > 0:
                z_scores_throughput = np.abs((throughput_values - throughput_mean) / throughput_std)
                outliers_throughput = z_scores_throughput > 2.0
            else:
                outliers_throughput = np.zeros(len(throughput_values), dtype=bool)
            
            # Combinar outliers (se for outlier em qualquer métrica)
            outliers_combined = outliers_tempo | outliers_throughput
            outliers_removidos += np.sum(outliers_combined)
            
            # Dados limpos (sem outliers)
            tempo_clean = tempo_values[~outliers_combined]
            throughput_clean = throughput_values[~outliers_combined]
            
            if len(tempo_clean) < 2:  # Precisa de pelo menos 2 valores após limpeza
                tempo_clean = tempo_values  # Usar dados originais se sobrar muito pouco
                throughput_clean = throughput_values
            
            # Calcular estatísticas completas
            stats_tempo = {
                'minimo': np.min(tempo_clean),
                'maximo': np.max(tempo_clean),
                'media': np.mean(tempo_clean),
                'mediana': np.median(tempo_clean),
                'desvio_padrao': np.std(tempo_clean, ddof=1) if len(tempo_clean) > 1 else 0,
                'outliers_removidos': np.sum(outliers_tempo)
            }
            
            stats_throughput = {
                'minimo': np.min(throughput_clean),
                'maximo': np.max(throughput_clean),
                'media': np.mean(throughput_clean),
                'mediana': np.median(throughput_clean),
                'desvio_padrao': np.std(throughput_clean, ddof=1) if len(throughput_clean) > 1 else 0,
                'outliers_removidos': np.sum(outliers_throughput)
            }
            
            # Adicionar aos resultados
            resultados_estatisticos.append({
                'Servidores': servidores,
                'Clientes': clientes,
                'Mensagens': mensagens,
                'Linguagem': linguagem,
                'Amostras_Originais': len(grupo_data),
                'Amostras_Limpas': len(tempo_clean),
                'Outliers_Removidos': np.sum(outliers_combined),
                
                # Estatísticas do Tempo de Resposta
                'Tempo_Min': stats_tempo['minimo'],
                'Tempo_Max': stats_tempo['maximo'],
                'Tempo_Media': stats_tempo['media'],
                'Tempo_Mediana': stats_tempo['mediana'],
                'Tempo_DesvPad': stats_tempo['desvio_padrao'],
                
                # Estatísticas do Throughput
                'Throughput_Min': stats_throughput['minimo'],
                'Throughput_Max': stats_throughput['maximo'],
                'Throughput_Media': stats_throughput['media'],
                'Throughput_Mediana': stats_throughput['mediana'],
                'Throughput_DesvPad': stats_throughput['desvio_padrao']
            })
        
        # Salvar análise estatística completa
        df_stats = pd.DataFrame(resultados_estatisticos)
        output_path = "../../resultados/relatorios/analise_estatistica_completa.csv"
        
        # Criar diretório se não existir
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        df_stats.to_csv(output_path, index=False, encoding='utf-8')
        
        # Salvar resumo executivo com estatísticas agregadas
        resumo_executivo = []
        
        # Análise por linguagem
        for linguagem in df['Linguagem'].unique():
            dados_lang = df[df['Linguagem'] == linguagem]
            
            if len(dados_lang) > 0:
                resumo_executivo.append({
                    'Categoria': 'Linguagem',
                    'Valor': linguagem,
                    'Total_Execucoes': len(dados_lang),
                    'Tempo_Medio_Geral': dados_lang['Tempo Médio (s)'].mean(),
                    'Tempo_Mediana_Geral': dados_lang['Tempo Médio (s)'].median(),
                    'Throughput_Medio_Geral': dados_lang['Throughput (req/s)'].mean(),
                    'Throughput_Mediana_Geral': dados_lang['Throughput (req/s)'].median()
                })
        
        # Análise por número de servidores
        for servidores in sorted(df['Servidores'].unique()):
            dados_serv = df[df['Servidores'] == servidores]
            
            if len(dados_serv) > 0:
                resumo_executivo.append({
                    'Categoria': 'Servidores',
                    'Valor': f"{servidores} servidor(es)",
                    'Total_Execucoes': len(dados_serv),
                    'Tempo_Medio_Geral': dados_serv['Tempo Médio (s)'].mean(),
                    'Tempo_Mediana_Geral': dados_serv['Tempo Médio (s)'].median(),
                    'Throughput_Medio_Geral': dados_serv['Throughput (req/s)'].mean(),
                    'Throughput_Mediana_Geral': dados_serv['Throughput (req/s)'].median()
                })
        
        # Análise por número de mensagens
        for mensagens in sorted(df['Mensagens'].unique()):
            dados_msg = df[df['Mensagens'] == mensagens]
            
            if len(dados_msg) > 0:
                resumo_executivo.append({
                    'Categoria': 'Mensagens',
                    'Valor': f"{mensagens} mensagem(s)",
                    'Total_Execucoes': len(dados_msg),
                    'Tempo_Medio_Geral': dados_msg['Tempo Médio (s)'].mean(),
                    'Tempo_Mediana_Geral': dados_msg['Tempo Médio (s)'].median(),
                    'Throughput_Medio_Geral': dados_msg['Throughput (req/s)'].mean(),
                    'Throughput_Mediana_Geral': dados_msg['Throughput (req/s)'].median()
                })
        
        # Salvar resumo executivo
        df_resumo = pd.DataFrame(resumo_executivo)
        resumo_path = "../../resultados/relatorios/resumo_executivo_estatisticas.csv"
        df_resumo.to_csv(resumo_path, index=False, encoding='utf-8')
        
        # Relatório de limpeza de dados
        print(f"\n=== RELATÓRIO DE ANÁLISE ESTATÍSTICA ===")
        print(f"Total de registros analisados: {len(df)}")
        print(f"Total de outliers removidos: {outliers_removidos}")
        print(f"Configurações de teste analisadas: {len(resultados_estatisticos)}")
        print(f"Arquivo gerado: {output_path}")
        print(f"Resumo executivo: {resumo_path}")
        
        # Verificar se atingimos 3000 execuções
        total_execucoes = len(df)
        configuracoes_esperadas = 5 * 10 * 6  # 300 configurações
        execucoes_esperadas = configuracoes_esperadas * 10  # 3000 execuções
        
        print(f"\n=== VERIFICAÇÃO DE CONFORMIDADE ===")
        print(f"Execuções realizadas: {total_execucoes}")
        print(f"Execuções esperadas: {execucoes_esperadas}")
        print(f"Percentual atingido: {(total_execucoes/execucoes_esperadas)*100:.1f}%")
        
        if total_execucoes >= execucoes_esperadas:
            print("✅ CONFORMIDADE ATINGIDA: 3000 execuções conforme especificação")
        else:
            print("❌ CONFORMIDADE PARCIAL: Não atingiu as 3000 execuções especificadas")
        
        return True
        
    except Exception as e:
        print(f"Erro na análise estatística: {e}")
        return False

if __name__ == "__main__":
    calcular_estatisticas_avancadas()
