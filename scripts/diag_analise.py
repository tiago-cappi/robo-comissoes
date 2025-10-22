import os, pandas as pd, unicodedata
p = os.path.join(os.getcwd(),'Analise_Comercial_Completa.csv')
out = os.path.join(os.getcwd(),'scripts','analise_diag.txt')
with open(out,'w',encoding='utf-8') as fh:
    fh.write(f'path={p}\nexists={os.path.exists(p)}\n')
    if not os.path.exists(p):
        fh.write('file missing\n')
    else:
        # read raw first 2000 chars
        with open(p,'rb') as rb:
            raw = rb.read(4000)
        fh.write('raw_bytes_preview=' + repr(raw[:4000]) + '\n')
        # try reading with common separators
        for sep in [';','\t',',']:
            try:
                df = pd.read_csv(p, sep=sep, engine='python', dtype=str, encoding='utf-8')
                fh.write(f'-- sep={sep} shape={df.shape} cols={list(df.columns)[:20]}\n')
            except Exception as e:
                fh.write(f'-- sep={sep} read_error={e}\n')
        # attempt to read with detected sep from preparador logic
        try:
            # simple detect with first line
            with open(p,'r',encoding='utf-8',errors='replace') as fhp:
                first = fhp.readline()
            counts = {',': first.count(','), ';': first.count(';'), '\t': first.count('\t')}
            sep = max(counts, key=lambda k: (counts[k], 1 if k==';' else 0))
            if counts[sep] == 0:
                sep = ','
            fh.write(f'detected_sep={repr(sep)} counts={counts}\n')
            df = pd.read_csv(p, sep=sep, engine='python', dtype=str, encoding='utf-8', on_bad_lines='warn')
            fh.write('read ok with detected sep; shape=' + str(df.shape) + '\n')
            cols = list(df.columns)
            fh.write('columns:\n')
            for c in cols[:200]:
                fh.write(' - ' + repr(c) + '\n')
            # find date candidates
            cands = [c for c in cols if 'dt' in c.lower() or 'emiss' in c.lower() or 'data' in c.lower()]
            fh.write('date candidates=' + repr(cands) + '\n')
            # show sample values for first candidate
            if cands:
                dc = cands[0]
                s = df[dc].astype(str).str.strip().str.replace('\u00a0',' ')
                fh.write('sample values for ' + repr(dc) + ':\n')
                for v in s.head(20):
                    fh.write(' - ' + repr(v) + '\n')
                # try parsing dates
                parsed1 = pd.to_datetime(s, dayfirst=True, errors='coerce')
                parsed2 = pd.to_datetime(s, dayfirst=False, errors='coerce')
                fh.write('parsed1 non-null=' + str(parsed1.notna().sum()) + ' parsed2 non-null=' + str(parsed2.notna().sum()) + '\n')
                # rows matching 8/2025
                sel = parsed1 if parsed1.isna().sum() <= parsed2.isna().sum() else parsed2
                selm = sel[ (sel.dt.month==8) & (sel.dt.year==2025) ]
                fh.write('rows with month=8 year=2025 count=' + str(len(selm)) + '\n')
                if len(selm)>0:
                    idxs = selm.index[:10].tolist()
                    fh.write('sample rows for matching idxs:\n')
                    fh.write(df.loc[idxs].to_string(index=False))
        except Exception as e:
            fh.write('detected read error: ' + repr(e) + '\n')
print('diag written to', out)
