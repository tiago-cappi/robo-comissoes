import preparar_dados_mensais as prep
f,c,y, r = prep.prepare_dataframes_for_month(8,2025)
print('faturados shape', None if f is None else f.shape)
print('conversoes shape', None if c is None else c.shape)
print('ytd shape', None if y is None else y.shape)
print('retencao shape', None if r is None else r.shape)

if f is not None and not f.empty:
    print('f sample:')
    print(f.head(5).to_string(index=False))
else:
    print('faturados is empty')

# print some raw columns available in loaded analise (internal)
import pandas as pd, os
p = os.path.join(os.getcwd(),'Analise_Comercial_Completa.csv')
sep, enc = prep._detect_sep(p)
df = pd.read_csv(p, sep=sep, engine='python', dtype=str, encoding=enc)
print('analise read shape', df.shape)
print('cols sample:', df.columns[:30].tolist())
# show values of Dt Emissao column if present
cands = [c for c in df.columns if 'emiss' in c.lower()]
print('emiss candidates', cands)
if cands:
    col = cands[0]
    s = df[col].astype(str).str.strip().str.replace('\u00a0',' ')
    print('sample emiss values non-empty count', s.replace('nan','').ne('').sum())
    print(s.head(10).to_string(index=False))
