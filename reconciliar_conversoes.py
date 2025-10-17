import pandas as pd
import unicodedata


def _norm(s):
    try:
        s2 = str(s)
        s2 = unicodedata.normalize('NFKD', s2)
        s2 = s2.encode('ASCII', 'ignore').decode()
        return ' '.join(s2.strip().lower().split())
    except Exception:
        return str(s).strip().lower()


def load_csv(path):
    for enc in ['utf-8-sig','utf-8','latin1']:
        try:
            df = pd.read_csv(path, sep=';', engine='python', encoding=enc, dtype=str)
            df.columns = [c.strip() for c in df.columns]
            return df
        except Exception:
            continue
    raise RuntimeError('Failed to read csv')


def main():
    gen = pd.read_excel('Conversões.xlsx')
    ref = pd.read_excel('Conversões Setembro 2025.xlsx')
    csv = load_csv('Analise_Comercial_Completa.csv')

    ref['__key'] = ref['Processo'].astype(str).fillna('') + '||' + ref['Código Produto'].astype(str).fillna('')
    gen['__key'] = gen['Processo'].astype(str).fillna('') + '||' + gen['Código Produto'].astype(str).fillna('')

    gen_keys = set(gen['__key'])
    missing_keys = [k for k in ref['__key'] if k not in gen_keys]

    rows = []
    for k in missing_keys:
        proc, code = k.split('||')
        ref_row = ref[ref['__key']==k].iloc[0].to_dict()
        csv_row = csv[csv['Processo'].astype(str).str.strip()==proc]
        csv_row_dict = csv_row.to_dict(orient='records') if len(csv_row)>0 else []
        rows.append({
            'Processo': proc,
            'Código Produto': code,
            'Ref_Operação': ref_row.get('Operação',''),
            'Ref_Data Aceite': ref_row.get('Data Aceite',''),
            'CSV_rows_count_for_processo': len(csv_row),
            'CSV_rows_sample': csv_row_dict[:3]
        })

    out = pd.DataFrame(rows)
    out.to_csv('conversoes_reconciliacao_missing.csv', index=False, encoding='utf-8-sig')
    print('Wrote conversoes_reconciliacao_missing.csv with', len(out), 'rows')

if __name__ == '__main__':
    main()
