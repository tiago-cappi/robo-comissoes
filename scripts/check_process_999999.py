import os
import pandas as pd

base = os.getcwd()
analise = os.path.join(base, 'Analise_Comercial_Completa.csv')
status = os.path.join(base, 'Status_Pagamentos_Processos.xlsx')
proc = '999999'

print('cwd:', base)
print('Analise exists?', os.path.exists(analise))
print('Status exists?', os.path.exists(status))

# Read Analise
try:
    df_anal = pd.read_csv(analise, sep=';', dtype=str, encoding='utf-8', engine='python')
except Exception as e:
    print('Failed to read Analise_Comercial_Completa.csv:', e)
    raise
print('Analise columns:', df_anal.columns.tolist())
print('Analise shape:', df_anal.shape)

if 'Processo' in df_anal.columns:
    df_a = df_anal[df_anal['Processo'].astype(str).str.strip() == proc]
else:
    # fallback: case-insensitive
    cols = {c.upper(): c for c in df_anal.columns}
    if 'PROCESSO' in cols:
        df_a = df_anal[df_anal[cols['PROCESSO']].astype(str).str.strip() == proc]
    else:
        df_a = pd.DataFrame()

print(f"Matches in Analise for {proc}: {len(df_a)} rows")
if len(df_a):
    # print key columns
    cols_to_show = ['Processo', 'Status Processo', 'Dt Emissão', 'Valor Realizado', 'Valor Orçado']
    for c in cols_to_show:
        if c in df_a.columns:
            print(c, '->', df_a[c].unique())
    print(df_a.head().to_string(index=False))

# Read Status_Pagamentos_Processos.xlsx
try:
    df_status = pd.read_excel(status, dtype=str)
except Exception as e:
    print('Failed to read Status_Pagamentos_Processos.xlsx:', e)
    raise

print('Status_Pagamentos columns:', df_status.columns.tolist())

# find PROCESSO-like and STATUS_PAGAMENTO-like columns
proc_col = next((c for c in df_status.columns if 'PROCESSO' in c.upper()), None)
status_col = next((c for c in df_status.columns if 'STATUS_PAGAMENTO' in c.upper() or ('STATUS' in c.upper() and 'PAG' in c.upper())), None)

print('Detected proc_col:', proc_col)
print('Detected status_col:', status_col)

if proc_col:
    df_s = df_status[df_status[proc_col].astype(str).str.strip() == proc]
else:
    df_s = pd.DataFrame()

print(f"Matches in Status_Pagamentos for {proc}: {len(df_s)} rows")
if len(df_s):
    if status_col and status_col in df_s.columns:
        print('STATUS_PAGAMENTO values ->', df_s[status_col].unique())
    print(df_s.to_string(index=False))

print('Done')
