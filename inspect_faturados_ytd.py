import glob, os, pandas as pd
candidates = ['Faturados_YTD.xlsx','Faturados_YTD_Setembro_2025.xlsx','Faturados_YTD_Setembro_2025.xls']
found = None
for c in candidates:
    p = os.path.join(os.getcwd(), c)
    if os.path.exists(p):
        found = p
        break
# try any matching
if not found:
    files = glob.glob(os.path.join(os.getcwd(), 'Faturados*YTD*.xlsx'))
    if files:
        files.sort(key=os.path.getmtime, reverse=True)
        found = files[0]
if not found:
    print('Nenhum arquivo Faturados_YTD encontrado no diretório atual.')
    raise SystemExit(1)
print('Usando:', found)
df = pd.read_excel(found)
print('Colunas:', df.columns.tolist())
# normalize fabricante column name
fab_cols = [c for c in df.columns if 'fabricante' in str(c).lower() or 'fornecedor' in str(c).lower()]
val_col = [c for c in df.columns if 'valor' in str(c).lower()]
if not fab_cols:
    print('Nenhuma coluna Fabricante/Fornecedor encontrada.')
else:
    fab = fab_cols[0]
    subset = df[df[fab].astype(str).str.upper().str.contains('YSI')]
    print('Linhas com Fabricante contendo YSI:', len(subset))
    if not subset.empty:
        print(subset.head(50).to_string(index=False))
# Summarize total by fabricante
if fab_cols:
    s = df.groupby(fab)[val_col[0]].sum().reset_index().sort_values(val_col[0], ascending=False)
    print('\nTop fabricantes por soma de valor:')
    print(s.head(30).to_string(index=False))
