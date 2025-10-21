import glob, os, sys
import pandas as pd

files = glob.glob('Comissoes_Calculadas_*.xlsx')
if not files:
    print('NO_OUTPUT')
    sys.exit(0)
files.sort(key=os.path.getmtime, reverse=True)
fn = files[0]
print('OUTPUT_FILE:' + fn)
try:
    df = pd.read_excel(fn, sheet_name='COMISSOES_CALCULADAS')
except Exception as e:
    print('READ_ERROR:' + str(e))
    sys.exit(1)
if df is None or df.empty:
    print('NO_ROWS')
    sys.exit(0)
subset = ['nome_colaborador', 'processo', 'cod_produto']
present = [c for c in subset if c in df.columns]
if len(present) < len(subset):
    print('MISSING_COLUMNS:' + ','.join(subset))
    print('Found columns: ' + ','.join(df.columns.tolist()))
    sys.exit(1)
dups = df[df.duplicated(subset=subset, keep=False)]
print('DUP_COUNT:' + str(len(dups)))
if len(dups) > 0:
    # print a small sample
    print(dups.head(20).to_csv(index=False))
else:
    print('NO_DUPLICATES')
