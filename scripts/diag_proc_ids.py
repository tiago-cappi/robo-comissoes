import glob, os, pandas as pd

print('cwd', os.getcwd())
# find files
status_fn = 'Status_Pagamentos_Processos.xlsx'
rec_mes_fn = 'Recebimentos_do_Mes.xlsx'
files = glob.glob(os.path.join(os.getcwd(), 'Comissoes_Calculadas_*.xlsx'))
files.sort()
out_fn = files[-1] if files else None

print('\nFiles found:')
print(' status:', os.path.exists(status_fn), status_fn)
print(' recebimentos:', os.path.exists(rec_mes_fn), rec_mes_fn)
print(' output:', out_fn)

if os.path.exists(status_fn):
    try:
        df_status = pd.read_excel(status_fn)
        print('\nStatus_Pagamentos_PROCESSO unique sample:', df_status['PROCESSO'].dropna().unique())
        print('dtypes:')
        print(df_status.dtypes)
        print('\nStatus head:')
        print(df_status.head().to_string())
    except Exception as e:
        print('Error reading status:', e)

if os.path.exists(rec_mes_fn):
    try:
        df_rec = pd.read_excel(rec_mes_fn)
        print('\nRecebimentos_do_Mes PROCESSO sample types:', df_rec['PROCESSO'].dropna().unique())
        print(df_rec.head().to_string())
    except Exception as e:
        print('Error reading recebimentos:', e)

if out_fn and os.path.exists(out_fn):
    try:
        xl = pd.ExcelFile(out_fn)
        print('\nOutput sheets:', xl.sheet_names)
        if 'COMISSOES_RECEBIMENTO' in xl.sheet_names:
            df_cr = pd.read_excel(out_fn, sheet_name='COMISSOES_RECEBIMENTO')
            print('\nCOMISSOES_RECEBIMENTO PROCESSO sample:', df_cr['processo'].dropna().unique())
            print(df_cr.to_string())
        if 'ESTADO' in xl.sheet_names:
            df_st = pd.read_excel(out_fn, sheet_name='ESTADO')
            print('\nESTADO PROCESSO unique sample:', df_st['PROCESSO'].dropna().unique())
            print(df_st.to_string())
    except Exception as e:
        print('Error reading output:', e)

print('\nDiagnostic done')
