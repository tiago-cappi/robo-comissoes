import os
import pandas as pd

base = os.getcwd()
estado = os.path.join(base, 'Estado_Processos_Recebimento.xlsx')
proc = '999999'
print('estado exists?', os.path.exists(estado))
if not os.path.exists(estado):
    print('Estado_Processos_Recebimento.xlsx not found; assuming reconciliation not yet confirmed')
else:
    try:
        df = pd.read_excel(estado, dtype=str)
    except Exception as e:
        print('Failed to read Estado_Processos_Recebimento.xlsx:', e)
        raise
    print('Columns:', df.columns.tolist())
    # find PROCESSO-like
    proc_col = next((c for c in df.columns if 'PROCESSO' in c.upper()), None)
    status_col = next((c for c in df.columns if 'RECONCIL' in c.upper() or 'CONFIRM' in c.upper() or 'ESTADO' in c.upper()), None)
    print('proc_col:', proc_col, 'status_col:', status_col)
    if proc_col:
        dfp = df[df[proc_col].astype(str).str.strip() == proc]
    else:
        dfp = pd.DataFrame()
    print('Matches:', len(dfp))
    if len(dfp):
        print(dfp.to_string(index=False))

print('Done')
