import glob, os, pandas as pd
files = glob.glob(os.path.join(os.getcwd(), 'Comissoes_Calculadas_*.xlsx'))
if not files:
    files = glob.glob(os.path.join(os.getcwd(), 'Comissoes_Calculadas_*.xls*'))
if not files:
    print('NO_OUTPUT_FILE')
    raise SystemExit(0)
files.sort(key=os.path.getmtime, reverse=True)
f = files[0]
print('FILE', f)
try:
    df = pd.read_excel(f, sheet_name='RECONCILIACAO')
except Exception as e:
    print('READ_ERROR', e)
    raise SystemExit(1)
if df is None or df.empty:
    print('NO_RECONCILIACAO_OR_EMPTY')
    raise SystemExit(0)
print('SHAPE', df.shape)
print('COLUMNS', list(df.columns))
print(df.head(20).to_string())
fc_cols = [c for c in df.columns if 'fator' in c.lower() or 'fc_' in c.lower() or c.lower().startswith('fc_') or 'comp_fc' in c.lower()]
print('FC_COLS', fc_cols)
for c in fc_cols:
    try:
        s = pd.to_numeric(df[c], errors='coerce')
        print(c, 'nan_count=', s.isna().sum(), 'unique_vals=', sorted(s.dropna().unique())[:10])
    except Exception as e:
        print('ERR_COL', c, e)
if 'row_type' in df.columns:
    print('ROW_TYPE_COUNTS')
    print(df['row_type'].value_counts().to_string())
for cand in ['fator_correcao_fc','fator_correcao','fator_correcao_fc_retro','comissao_calculada_retro']:
    if cand in df.columns:
        s = df[df[cand] != 1]
        print('SAMPLE rows with', cand, '!=1 ->', len(s))
        if not s.empty:
            print(s.head(5).to_string())
print('DONE')
