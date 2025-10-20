import pandas as pd, re, unicodedata

df = pd.read_excel('fin_conci_adcli_m3.xls')

def norm(s):
    s=str(s).strip().lower()
    s=unicodedata.normalize('NFKD', s)
    s=s.encode('ASCII','ignore').decode()
    s=re.sub(r'[^a-z0-9]+','_',s)
    return s

mp={c:norm(c) for c in df.columns}
df=df.rename(columns=mp)

if 'vl_original' in df.columns:
    df['vl_original']=df['vl_original'].astype(str).str.extract(r'((?:\d{4}-\d{2}-\d{2})|(?:\d{2}/\d{2}/\d{4}))', expand=False)


def extrair_processo(texto_documento):
    if isinstance(texto_documento, str):
        texto_base = texto_documento.split('/')[0]
        m = re.search(r'\d+', texto_base)
        if m:
            return m.group(0)
    return None

cnt=0
rows=[]
for _,row in df.iterrows():
    data_val=row.get('vl_original')
    try:
        data_receb=pd.to_datetime(data_val, errors='coerce')
    except Exception:
        data_receb=pd.NaT
    valor=row.get('vl_baixado')
    proc_this=extrair_processo(row.get('filial'))
    if valor is not None and pd.notna(data_receb) and proc_this:
        cnt+=1
        rows.append((proc_this, data_receb, valor))

print('valid_rows',cnt)
print('sample', rows[:5])
