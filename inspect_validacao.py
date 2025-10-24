import glob, os, pandas as pd
files = glob.glob(os.path.join(os.getcwd(), 'Comissoes_Calculadas_*.xlsx'))
if not files:
    print('Nenhum arquivo de saida encontrado')
    raise SystemExit(1)
files.sort(key=os.path.getmtime, reverse=True)
file = files[0]
print('Usando', file)
xls = pd.ExcelFile(file)
if 'VALIDACAO' in [s.upper() for s in xls.sheet_names]:
    s = next(s for s in xls.sheet_names if s.upper()=='VALIDACAO')
    df = pd.read_excel(file, sheet_name=s)
    print('Linhas VALIDACAO:', len(df))
    # print avisos containing 'anômalo' or 'anomalo' or 'faturamento_realizado'
    if not df.empty:
        mask = df['Mensagem'].astype(str).str.contains('anomalo|anômalo|faturamento_realizado|recomputed', case=False, na=False)
        if mask.any():
            print(df[mask].to_string(index=False))
        else:
            print('Nenhuma mensagem de validação relacionada encontrada.')
else:
    print('Aba VALIDACAO nao encontrada. Abas disponiveis:', xls.sheet_names)
