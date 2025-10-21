import glob, os, pandas as pd
files = glob.glob('Comissoes_Calculadas_*.xlsx')
if not files:
    print('NO_OUTPUT')
    raise SystemExit(0)
files.sort(key=os.path.getmtime, reverse=True)
fn = files[0]
print('FILE:', fn)
df = pd.read_excel(fn, sheet_name='COMISSOES_CALCULADAS')
cols_needed = ['nome_colaborador','processo','cod_produto','realizado_rentab','meta_rentab','ating_rentab']
present = [c for c in cols_needed if c in df.columns]
print('PRESENT:', present)
if not all(c in df.columns for c in ['realizado_rentab','meta_rentab','ating_rentab']):
    print('MISSING RENTAB COLUMNS')
    raise SystemExit(0)
# coerce to numeric
for c in ['realizado_rentab','meta_rentab','ating_rentab']:
    df[c] = pd.to_numeric(df[c], errors='coerce')
mask = df['realizado_rentab'] > df['meta_rentab']
res = df[mask][['nome_colaborador','processo','cod_produto','realizado_rentab','meta_rentab','ating_rentab']]
print('TOTAL_ROWS_REALIZADO_GT_META:', len(res))
if len(res)>0:
    print(res.head(20).to_string(index=False))
else:
    print('NO_ROWS')
