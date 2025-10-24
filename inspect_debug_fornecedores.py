import glob
import os
import pandas as pd

pattern = os.path.join(os.getcwd(), 'Comissoes_Calculadas_*.xlsx')
files = glob.glob(pattern)
if not files:
    # try searching recursively
    files = glob.glob(os.path.join(os.getcwd(), '**', 'Comissoes_Calculadas_*.xlsx'), recursive=True)
if not files:
    print('Nenhum arquivo Comissoes_Calculadas_*.xlsx encontrado no workspace.')
    raise SystemExit(1)
# pick latest
files.sort(key=os.path.getmtime, reverse=True)
file = files[0]
print(f'Usando arquivo: {file}')

xls = pd.ExcelFile(file)
sheets = xls.sheet_names
if 'debug_fornecedores' not in [s.lower() for s in sheets]:
    print('Aba debug_fornecedores não encontrada. Abas disponíveis:')
    print('\n'.join(sheets))
    # try to find a sheet with 'fornecedor' in name
    for s in sheets:
        if 'fornecedor' in s.lower() or 'debug' in s.lower():
            print(f"Tentando abrir sheet: {s}")
            df = pd.read_excel(file, sheet_name=s)
            break
    else:
        raise SystemExit(1)
else:
    # find actual sheet name matching lower-case
    sname = next(s for s in sheets if s.lower() == 'debug_fornecedores')
    df = pd.read_excel(file, sheet_name=sname)

# normalize column names
cols = {c: c.strip() for c in df.columns}
df.rename(columns=cols, inplace=True)
# ensure numeric
if 'faturamento_realizado_ytd' in df.columns:
    df['faturamento_realizado_ytd'] = pd.to_numeric(df['faturamento_realizado_ytd'], errors='coerce').fillna(0.0)

print('\nTop 30 entries by faturamento_realizado_ytd:')
if 'faturamento_realizado_ytd' in df.columns:
    print(df.sort_values('faturamento_realizado_ytd', ascending=False).head(30).to_string(index=False))
else:
    print('Coluna faturamento_realizado_ytd não encontrada.')

# show entries for fornecedor YSI if present
if 'fornecedor' in df.columns:
    ysi = df[df['fornecedor'].astype(str).str.upper().str.contains('YSI')]
    if not ysi.empty:
        print('\nEntradas para fornecedor contendo YSI:')
        print(ysi.to_string(index=False))
    else:
        print('\nNenhuma entrada para fornecedor YSI encontrada no debug_fornecedores.')

# also show any rows with extremely large values
if 'faturamento_realizado_ytd' in df.columns:
    large = df[df['faturamento_realizado_ytd'].abs() > 1e6]
    if not large.empty:
        print('\nEntradas com faturamento_realizado_ytd > 1e6:')
        print(large.to_string(index=False))
