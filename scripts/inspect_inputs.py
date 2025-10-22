import importlib.util
import os
import pandas as pd

# import calculo_comissoes by absolute path to work from scripts/ subfolder
root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
mod_path = os.path.join(root, 'calculo_comissoes.py')
spec = importlib.util.spec_from_file_location('calculo_comissoes', mod_path)
calc_mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(calc_mod)
CalculoComissao = calc_mod.CalculoComissao

c = CalculoComissao()
# run loader
c._carregar_dados()
import os
print('\nCurrent working directory:', os.getcwd())
print('Files in cwd:')
for f in sorted(os.listdir(os.getcwd())):
    print(' -', f)
keys = ['FATURADOS','CONVERSOES','RENTABILIDADE_REALIZADA','METAS_APLICACAO','METAS_INDIVIDUAIS','META_RENTABILIDADE','METAS_FORNECEDORES','PESOS_METAS','CONFIG_COMISSAO','ANALISE_COMERCIAL_COMPLETA']
for k in keys:
    df = c.data.get(k)
    if df is None:
        print(f"{k}: None")
        continue
    if isinstance(df, pd.DataFrame):
        print(f"{k}: shape={df.shape}")
        # print first rows safely
        try:
            print(df.head(5).to_string(index=False))
        except Exception:
            print(df.head(3))
    else:
        print(f"{k}: (not a DataFrame) type={type(df)}")

# print some derived stuff
try:
    c._preprocessar_dados()
    c._calcular_realizado()
    print('\nDerived realizado keys:')
    for k,v in c.realizado.items():
        try:
            if isinstance(v, pd.Series):
                print(f"{k}: series len={len(v)} top=\n{v.head(3)}")
            else:
                print(f"{k}: type={type(v)}")
        except Exception as e:
            print(f"Error printing {k}: {e}")
except Exception as e:
    print('Error in preprocess/realizado:', e)

print('\nParams sample:')
print({k:c.params.get(k) for k in ('cap_atingimento_max','cap_fc_max','taxa_rateio_maximo_pct','fatia_cargo_pct')})
print('\nPESOS_METAS head:')
pm = c.data.get('PESOS_METAS')
if isinstance(pm, pd.DataFrame):
    try:
        print(pm.head(10).to_string(index=False))
    except Exception:
        print(pm.head(5))
else:
    print(pm)
