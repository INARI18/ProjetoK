import os
import glob
import sys
import pandas as pd

def main():
    print('[DEBUG] Início do main()')
    if len(sys.argv) < 2:
        print('[DEBUG] Argumentos insuficientes (esperado pelo menos 2)')
        print('Uso: python merge_csv_results.py <diretorio_temp> [arquivo_saida]')
        sys.exit(1)
    if len(sys.argv) < 3:
        print('[DEBUG] Argumentos insuficientes (esperado pelo menos 3)')
        print('Uso: python merge_csv_results.py <diretorio_temp> <linguagem> [arquivo_saida]')
        print('linguagem: go ou python')
        sys.exit(1)
    temp_dir = sys.argv[1]
    linguagem = sys.argv[2].lower()
    if not os.path.isdir(temp_dir):
        print(f'[DEBUG] Diretório não encontrado: {temp_dir}')
        sys.exit(1)
    csvs = sorted(glob.glob(os.path.join(temp_dir, '*.csv')))
    if not csvs:
        print(f'[DEBUG] Nenhum arquivo CSV encontrado em {temp_dir}')
        sys.exit(1)

    print(f'[DEBUG] Chamando merge para linguagem: {linguagem}')
    if linguagem == 'go':
        merge_go(csvs, temp_dir)
    elif linguagem == 'python':
        merge_python(csvs, temp_dir)
    else:
        print('[DEBUG] Linguagem não suportada. Use "go" ou "python".')
        sys.exit(1)
    print('[DEBUG] Fim do main()')

def merge_go(csvs, temp_dir):
    dfs = []
    colunas_padrao = [
        "cenario_id","repeticao","cliente_id","num_clientes","num_servidores","num_mensagens",
        "tempo_inicio","tempo_fim","tempo_total_ms","status","erro","mem_mb","num_goroutine"
    ]
    for path in csvs:
        df = pd.read_csv(path)
        for col in colunas_padrao:
            if col not in df.columns:
                df[col] = ""
        df = df[colunas_padrao]
        dfs.append(df)
    final = pd.concat(dfs, ignore_index=True)
    if all(col in final.columns for col in ["cenario_id", "repeticao", "cliente_id"]):
        final["_cenario_id_num"] = final["cenario_id"].astype(str).str.extract(r'(\d+)').astype(int)
        final["_repeticao_num"] = final["repeticao"].astype(int)
        final["_cliente_id_num"] = final["cliente_id"].astype(int)
        final = final.sort_values(by=["_cenario_id_num", "_repeticao_num", "_cliente_id_num"]).reset_index(drop=True)
        final = final.drop(columns=["_cenario_id_num", "_repeticao_num", "_cliente_id_num"])
    if len(sys.argv) > 3:
        final_path = sys.argv[3]
    else:
        final_path = os.path.join(os.path.dirname(temp_dir), 'test-go.csv')
    final = final[colunas_padrao]
    final.to_csv(final_path, index=False)
    print(f'Merge concluído! Arquivo final: {final_path} ({len(final)} linhas)')

def merge_python(csvs, temp_dir):
    print(f"[DEBUG] Iniciando merge_python com {len(csvs)} arquivos em {temp_dir}")
    dfs = []
    colunas_padrao = [
        "cenario_id","repeticao","cliente_id","num_clientes","num_servidores","num_mensagens",
        "tempo_inicio","tempo_fim","tempo_total_ms","status","erro","mem_mb"
    ]
    for path in csvs:
        df = pd.read_csv(path)
        for col in colunas_padrao:
            if col not in df.columns:
                df[col] = ""
        df = df[colunas_padrao]
        dfs.append(df)
    final = pd.concat(dfs, ignore_index=True)
    if all(col in final.columns for col in ["cenario_id", "repeticao", "cliente_id"]):
        final["_cenario_id_num"] = final["cenario_id"].astype(str).str.extract(r'(\d+)').astype(int)
        final["_repeticao_num"] = final["repeticao"].astype(int)
        final["_cliente_id_num"] = final["cliente_id"].astype(int)
        final = final.sort_values(by=["_cenario_id_num", "_repeticao_num", "_cliente_id_num"]).reset_index(drop=True)
        final = final.drop(columns=["_cenario_id_num", "_repeticao_num", "_cliente_id_num"])
    if len(sys.argv) > 3:
        final_path = sys.argv[3]
    else:
        final_path = os.path.join(os.path.dirname(temp_dir), 'test-python.csv')
    final = final[colunas_padrao]
    final.to_csv(final_path, index=False)
    print(f'[DEBUG] Merge concluído! Arquivo final: {final_path} ({len(final)} linhas)')


if __name__ == "__main__":
    main()
