import glob, os, pandas as pd, ast

# find latest Comissoes_Calculadas
pattern = os.path.join(os.getcwd(), 'Comissoes_Calculadas_*.xlsx')
files = glob.glob(pattern)
if not files:
    files = glob.glob(os.path.join(os.getcwd(), '**', 'Comissoes_Calculadas_*.xlsx'), recursive=True)
if not files:
    print('Nenhum arquivo Comissoes_Calculadas_*.xlsx encontrado.')
    raise SystemExit(1)
files.sort(key=os.path.getmtime, reverse=True)
file = files[0]
print('Usando arquivo:', file)
xls = pd.ExcelFile(file)
# find debug_fornecedores sheet
sname = None
# prefer sheet with fornecedor in name
for s in xls.sheet_names:
    if 'forneced' in s.lower() or 'fornecedor' in s.lower():
        sname = s
        break
# fallback: any sheet with 'debug' in name
if sname is None:
    for s in xls.sheet_names:
        if 'debug' in s.lower():
            sname = s
            break
if sname is None:
    print('Nenhuma sheet debug encontrada. Abas:', xls.sheet_names)
    raise SystemExit(1)
print('Abrindo sheet:', sname)
df_debug = pd.read_excel(file, sheet_name=sname)
print('Linhas debug:', len(df_debug))
# normalize columns
df_debug.columns = [c.strip() for c in df_debug.columns]
# find YSI rows
if 'fornecedor' in df_debug.columns:
    ysi = df_debug[df_debug['fornecedor'].astype(str).str.upper().str.contains('YSI')]
    print('Linhas YSI debug:', len(ysi))
else:
    print('Sem coluna fornecedor')
    raise SystemExit(1)

# load FATURADOS_YTD
f_candidates = ['Faturados_YTD.xlsx','Faturados_YTD_Setembro_2025.xlsx']
found = None
for c in f_candidates:
    p = os.path.join(os.getcwd(), c)
    if os.path.exists(p):
        found = p
        break
if not found:
    files = glob.glob(os.path.join(os.getcwd(), 'Faturados*YTD*.xlsx'))
    if files:
        files.sort(key=os.path.getmtime, reverse=True)
        found = files[0]
if not found:
    print('FATURADOS_YTD não encontrado')
    raise SystemExit(1)
print('Usando FATURADOS_YTD:', found)
df_ytd = pd.read_excel(found)
# normalize columns
df_ytd.columns = [c.strip() for c in df_ytd.columns]
# determine fabricante column and value column
fab_col = next((c for c in df_ytd.columns if 'fabricante' in c.lower() or 'fornecedor' in c.lower()), None)
val_col = next((c for c in df_ytd.columns if 'valor' in c.lower()), None)
dt_col = next((c for c in df_ytd.columns if 'dt' in c.lower() or 'data' in c.lower()), None)
print('fab_col, val_col, dt_col =', fab_col, val_col, dt_col)

for idx, row in ysi.iterrows():
    print('\n--- Debug row index', idx, '---')
    print(row.to_dict())
    taxas_s = row.get('taxas_usadas', None)
    print('taxas_usadas (raw):', taxas_s)
    taxas = {}
    if isinstance(taxas_s, str) and taxas_s.strip():
        try:
            taxas = ast.literal_eval(taxas_s)
        except Exception:
            # sometimes string like '{1: 0.16512, ...}' should parse; fallback: replace True/False?
            try:
                taxas = eval(taxas_s, {})
            except Exception as e:
                print('Não consegui parsear taxas_usadas:', e)
                taxas = {}
    print('taxas parsed:', taxas)
    fornecedor = row.get('fornecedor')
    # compute soma_brl per month from FATURADOS_YTD
    filt = df_ytd[df_ytd[fab_col].astype(str).str.upper().str.contains(str(fornecedor).upper())]
    print('Linhas em FATURADOS_YTD para este fornecedor:', len(filt))
    if filt.empty:
        print('Nenhuma linha encontrada no FATURADOS_YTD para fornecedor', fornecedor)
        continue
    if dt_col and dt_col in filt.columns:
        filt['mes'] = pd.to_datetime(filt[dt_col], errors='coerce').dt.month
    else:
        filt['mes'] = int(row.get('mes_apuracao', 0))
    # show per-month sums
    per = filt.groupby('mes')[val_col].sum().reset_index()
    print('Per-month sums from FATURADOS_YTD:')
    print(per.to_string(index=False))
    # compute converted sums using taxas dict if available
    total_conv = 0.0
    for m in range(1, int(row.get('mes_apuracao', 0)) + 1):
        soma = per[per['mes'] == m][val_col].sum() if not per.empty else 0.0
        taxa_m = None
        if isinstance(taxas, dict) and m in taxas:
            taxa_m = taxas[m]
        print(f'month={m} soma_brl={soma} taxa={taxa_m}')
        if taxa_m and taxa_m != 0:
            total_conv += float(soma) * float(taxa_m)
    print('total_conv computed:', total_conv)
    print('debug faturamento_realizado_ytd in sheet:', row.get('faturamento_realizado_ytd'))
