import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from calculo_comissoes import CalculoComissao
import pandas as pd

# Setup minimal instance
c = CalculoComissao()
# Minimal data
c.data = {
    'ANALISE_COMERCIAL_COMPLETA': pd.DataFrame([{'Processo': 'P1', 'Status Processo': 'Faturado', 'Dt Emissão': '2025-08-15', 'Negócio': 'L1', 'Grupo': 'G1', 'Subgrupo': 'S1', 'Tipo de Mercadoria': 'T1'}]),
    'STATUS_PAGAMENTOS': pd.DataFrame([{'PROCESSO': 'P1', 'STATUS_PAGAMENTO': 'Quitado'}]),
    'CONFIG_COMISSAO': pd.DataFrame([{'linha':'L1','grupo':'G1','subgrupo':'S1','tipo_mercadoria':'T1','cargo':'Gerente Linha','taxa_rateio_maximo_pct':5,'fatia_cargo_pct':20}]),
    'PESOS_METAS': pd.DataFrame([{'cargo':'Gerente Linha','faturamento_linha':50,'rentabilidade':50}]),
    'METAS_APLICACAO': pd.DataFrame([{'linha':'L1','tipo_mercadoria':'T1','tipo_meta':'faturamento','valor_meta':100.0}]),
    'METAS_INDIVIDUAIS': pd.DataFrame(),
    'META_RENTABILIDADE': pd.DataFrame(),
}
# estado with zero adiantamento
c.estado = pd.DataFrame([{'PROCESSO':'P1','VALOR_TOTAL_PROCESSO':100.0,'TOTAL_PAGO_ACUMULADO':0.0,'TOTAL_ADIANTADO_COMISSAO':0.0,'STATUS_RECONCILIACAO':'Nao Realizada','STATUS_PROCESSO_ANALISE':'Faturado'}])
# comissoes_df: contains one operational row for process
c.comissoes_df = pd.DataFrame([{
    'id_colaborador':'C1','nome_colaborador':'Op1','cargo':'Gerente Linha','cod_produto':'PR1','descricao_produto':'Prod','processo':'P1','linha':'L1','grupo':'G1','subgrupo':'S1','tipo_mercadoria':'T1','faturamento_item':100.0,'taxa_rateio_aplicada':0.05,'percentual_elegibilidade_pe':0.2,'tipo_lancamento':None
}])
# comissoes_recebimento_df: the 'recebimento' collaborator
c.comissoes_recebimento_df = pd.DataFrame([{
    'id_colaborador':'C2','nome_colaborador':'Receb1','cargo':'Gerente Linha','processo':'P1','linha':'L1','grupo':'G1','subgrupo':'S1','tipo_mercadoria':'T1','faturamento_item':25.0,'taxa_rateio_aplicada':0.05,'percentual_elegibilidade_pe':0.2,'tipo_lancamento':'Recebimento'
}])
# mark who receives by recebimento
c.recebe_por_recebimento = {'Receb1'}
# Monkeypatch _calcular_fc_retroativo_for_item to return non-1 FC so we can see detail rows
def fake_fc(nome_colab, cargo_colab, item_faturado, historic_data, mes_fat, ano_fat):
    return 0.85, {'faturamento_linha': {'componente_fc':0.5}, 'meta_fornecedor_1': {'componente_fc':0.35}}
c._calcular_fc_retroativo_for_item = fake_fc

# Run reconciliations
c._executar_reconciliacoes()
print('RECONCILIACAO DF:')
print(c.reconciliacao_df)

# Save to temp excel to inspect if needed
c.reconciliacao_df.to_excel('test_reconc_output.xlsx', index=False)
print('WROTE test_reconc_output.xlsx')
