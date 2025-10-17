import glob
import pandas as pd
import os

files = sorted(glob.glob('Comissoes_Calculadas_*.xlsx'))
if not files:
    print('Nenhum arquivo de Comissoes_Calculadas_*.xlsx encontrado')
    raise SystemExit(1)
path = files[-1]
print('Analisando:', path)

xls = pd.read_excel(path, sheet_name=None)
print('Abas encontradas:', list(xls.keys()))

# Mostrar resumo das abas relevantes
for sheet in ['COMISSOES_RECEBIMENTO', 'COMISSOES_CALCULADAS']:
    if sheet in xls:
        df = xls[sheet]
        print(f"\nSheet {sheet}: rows={len(df)} cols={list(df.columns)}")
        print(df.head(5).to_string(index=False))
    else:
        print(f"\nSheet {sheet} não encontrada")

# Comparar chaves
if 'COMISSOES_RECEBIMENTO' in xls and 'COMISSOES_CALCULADAS' in xls:
    dr = xls['COMISSOES_RECEBIMENTO']
    dc = xls['COMISSOES_CALCULADAS']
    def normalize(x):
        if pd.isna(x):
            return ''
        return str(x).strip()
    keys_r = set((normalize(r.get('processo')), normalize(r.get('nome_colaborador'))) for _, r in dr.iterrows())
    keys_c = set((normalize(r.get('processo')), normalize(r.get('nome_colaborador'))) for _, r in dc.iterrows())
    inter = keys_r & keys_c
    only_r = keys_r - keys_c
    only_c = keys_c - keys_r
    print(f"\nCOMPARAÇÃO: recebimento_rows={len(keys_r)} comissoes_rows={len(keys_c)} intersec={len(inter)} only_recebimento={len(only_r)} only_comissoes={len(only_c)}")
    print('\nExemplos interseção (até 10):')
    for i, k in enumerate(list(inter)[:10]):
        print(k)
    print('\nExemplos em recebimento mas não em comissoes (até 10):')
    for i, k in enumerate(list(only_r)[:10]):
        print(k)
    print('\nExemplos em comissoes mas não em recebimento (até 10):')
    for i, k in enumerate(list(only_c)[:10]):
        print(k)

# Mostrar nomes únicos e quaisquer diferenças em espaçamento/case
if 'COMISSOES_RECEBIMENTO' in xls:
    nr = set(str(x).strip() for x in xls['COMISSOES_RECEBIMENTO']['nome_colaborador'].dropna().unique())
else:
    nr = set()
if 'COMISSOES_CALCULADAS' in xls:
    nc = set(str(x).strip() for x in xls['COMISSOES_CALCULADAS']['nome_colaborador'].dropna().unique())
else:
    nc = set()
print('\nNomes únicos em RECEBIMENTO (count):', len(nr))
print(sorted(list(nr))[:20])
print('\nNomes únicos em CALCULADAS (count):', len(nc))
print(sorted(list(nc))[:20])

# Detect trivial differences (case-insensitive)
ci_r = set(x.lower() for x in nr)
ci_c = set(x.lower() for x in nc)
print('\nInterseção case-insensitive:', len(ci_r & ci_c))
print('Only recebimento (case-insensitive) examples:', list(ci_r - ci_c)[:10])
print('Only calculadas (case-insensitive) examples:', list(ci_c - ci_r)[:10])
