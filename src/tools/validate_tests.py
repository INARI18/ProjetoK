import os
import pandas as pd
from glob import glob


def get_expected_counts_by_matrix(df):
  
    servidores_validos = [2, 4, 6, 8, 10]
    clientes_validos = list(range(10, 101, 10))
    mensagens_validas = [1, 10, 100, 500, 1000, 10000]
    repeticoes_validas = list(range(1, 11))
    expected = {}
    for nservidores in servidores_validos:
        for nclientes in clientes_validos:
            for nmsg in mensagens_validas:
                for rep in repeticoes_validas:
                    expected[(nservidores, nclientes, nmsg, rep)] = nclientes
    return expected

def validate_file(path):
    df = pd.read_csv(path)
    total_exec = len(df)
    expected = get_expected_counts_by_matrix(df)
    total_expected = sum(expected.values())
    # Agrupa execuções reais por cenário
    real_counts = df.groupby(['num_servidores', 'num_clientes', 'num_mensagens', 'repeticao'])['cliente_id'].nunique()
    faltando = []
    for key, nclientes_esperado in expected.items():
        nservidores, nclientes, nmsg, rep = key
        nclientes_real = real_counts.get((nservidores, nclientes, nmsg, rep), 0)
        if nclientes_real < nclientes_esperado:
            faltando.append(f"Faltando clientes em servidores={nservidores}, clientes={nclientes}, mensagens={nmsg}, repetição={rep}: {nclientes_real}/{nclientes_esperado}")
    percent = ((total_expected - len(faltando)) / total_expected) * 100 if total_expected > 0 else 0
    print(f"Arquivo: {os.path.basename(path)}")
    print(f"Execuções registradas: {total_exec}")
    print(f"Execuções esperadas: {total_expected}")
    print(f"Cobertura de cenários completos: {percent:.2f}%\n")
    if faltando:
        for msg in faltando[:10]:
            print(msg)
        if len(faltando) > 10:
            print(f"...e mais {len(faltando)-10} cenários incompletos omitidos.")
    print()

def main():
    base_dir = os.path.dirname(__file__)
    reports_dir = os.path.join(base_dir, '..', 'results', 'reports')
    files = glob(os.path.join(reports_dir, 'test-*.csv'))
    if not files:
        print("Nenhum arquivo test-*.csv encontrado.")
        return
    for path in files:
        validate_file(path)

if __name__ == "__main__":
    main()
