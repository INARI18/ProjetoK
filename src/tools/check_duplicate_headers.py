import os
import glob

def check_duplicate_headers(temp_dir):
    csvs = sorted(glob.glob(os.path.join(temp_dir, '*.csv')))
    header_line = None
    for path in csvs:
        with open(path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            if not lines:
                print(f'[AVISO] Arquivo vazio: {path}')
                continue
            header = lines[0].strip()
            if header_line is None:
                header_line = header
            for i, line in enumerate(lines[1:], 2):
                if line.strip() == header:
                    print(f'[ERRO] Cabeçalho duplicado na linha {i} do arquivo: {path}')
    print('Verificação concluída.')

if __name__ == '__main__':
    pasta = r'src/results/reports/temp-py'  # ajuste se necessário
    check_duplicate_headers(pasta)
