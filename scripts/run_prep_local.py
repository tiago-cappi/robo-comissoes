import importlib.util, os, pandas as pd
root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
mod_path = os.path.join(root, 'preparar_dados_mensais.py')
spec = importlib.util.spec_from_file_location('preparar_dados_mensais', mod_path)
prep = importlib.util.module_from_spec(spec)
spec.loader.exec_module(prep)
print('module loaded:', hasattr(prep, 'prepare_dataframes_for_month'))
# read analise with detect sep
p = os.path.join(root, 'Analise_Comercial_Completa.csv')
sep, enc = prep._detect_sep(p)
df = pd.read_csv(p, sep=sep, engine='python', dtype=str, encoding=enc)
print('Analise shape:', df.shape)
cols = list(df.columns)
print('columns sample:', cols[:40])
# find best date col by matching
date_candidates = [c for c in cols if 'dt' in c.lower() or 'emiss' in c.lower() or 'data' in c.lower()]
print('date candidates:', date_candidates)
for c in date_candidates:
    s = df[c].astype(str).str.strip().str.replace('\u00a0',' ')
    p1 = pd.to_datetime(s, dayfirst=True, errors='coerce')
    p2 = pd.to_datetime(s, dayfirst=False, errors='coerce')
    print('\ncol:',repr(c))
    print(' sample vals:', s.head(10).tolist())
    print('parsed1 non-null:', p1.notna().sum(), 'parsed2 non-null:', p2.notna().sum())
    chosen = p1 if p1.isna().sum() <= p2.isna().sum() else p2
    print('chosen non-null:', chosen.notna().sum())
    print('chosen unique months:', sorted(chosen.dropna().dt.month.unique().tolist()))

# Now call helper and inspect returned faturados_df
f, c, y, r = prep.prepare_dataframes_for_month(8,2025)
print('\nprepare_dataframes_for_month returns shapes:', None if f is None else f.shape, None if c is None else c.shape, None if y is None else y.shape, None if r is None else r.shape)
if f is not None and not f.empty:
    print('f sample head:')
    print(f.head(10).to_string(index=False))
else:
    print('FATURADOS empty or None')
