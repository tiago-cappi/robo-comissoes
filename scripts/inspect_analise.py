import pandas as pd, os
p = os.path.join(os.getcwd(),'Analise_Comercial_Completa.csv')
print('path exists', os.path.exists(p))
# try detect sep
with open(p,'r',encoding='utf-8',errors='replace') as fh:
    first = fh.readline()
    print('first line sample:', first[:200])
# try read with semicolon
try:
    df = pd.read_csv(p, sep=';', engine='python', dtype=str)
    print('read with ; shape', df.shape)
except Exception as e:
    print('read ; error', e)
# try to show possible date column names
print('columns:', df.columns[:50].tolist())
# find date col candidates
cands = [c for c in df.columns if 'dt' in c.lower() or 'emiss' in c.lower() or 'data' in c.lower()]
print('date candidates:', cands[:10])
if cands:
    for c in cands[:3]:
        s = pd.to_datetime(df[c].astype(str).str.strip().str.replace('\u00a0',' '), dayfirst=True, errors='coerce')
        print(c, 'parsed non-null', s.notna().sum(), 'unique months:', sorted(s.dropna().dt.month.unique().tolist())[:10])
        print('sample parsed:', s.dropna().head(5))
print('\nshow head rows:')
print(df.head(10).to_string(index=False))
