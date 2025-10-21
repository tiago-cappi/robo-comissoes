import glob, os, pandas as pd
files = glob.glob('Comissoes_Calculadas_*.xlsx')
if not files:
    print('NO_OUTPUT')
    raise SystemExit(0)
files.sort(key=os.path.getmtime, reverse=True)
fn = files[0]
print('FILE:', fn)
df = pd.read_excel(fn, sheet_name='COMISSOES_CALCULADAS')
cols = [c for c in df.columns if 'rentab' in c]
print('RENTAB_COLUMNS:', cols)
if cols:
    print(df[cols].head(10).to_string(index=False))
