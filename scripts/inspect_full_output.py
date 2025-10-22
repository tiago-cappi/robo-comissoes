import glob
import os
import pandas as pd

files = glob.glob(os.path.join(os.getcwd(), 'Comissoes_Calculadas_*.xlsx'))
if not files:
    print('No output files found')
    raise SystemExit(1)
# pick the most recent
files.sort()
fn = files[-1]
print('FILE', fn)
xl = pd.ExcelFile(fn)
print('SHEETS:', xl.sheet_names)
for s in xl.sheet_names:
    try:
        df = pd.read_excel(fn, sheet_name=s)
        print('\n=== SHEET:', s, 'shape=', df.shape)
        print('COLUMNS:', df.columns.tolist())
        print('HEAD:')
        if df.shape[0] > 0:
            print(df.head(3).to_string())
        else:
            print('<empty>')
    except Exception as e:
        print('Error reading sheet', s, ':', e)
