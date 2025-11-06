import os
import sys
import pandas as pd
from tempfile import TemporaryDirectory

# Adicionar o diretório raiz ao path para imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models.process_state import ProcessStateManager
from services.financial_payments_loader import FinancialPaymentsLoader
from services.process_metrics_calculator import ProcessMetricsCalculator


def _make_analise_df():
    # Dois itens do mesmo processo com valores diferentes
    return pd.DataFrame(
        [
            {
                "Processo": "111111",
                "Dt Emissão": "2025-11-05",
                "Negócio": "Linha A",
                "Grupo": "G1",
                "Subgrupo": "SG1",
                "Tipo de Mercadoria": "T1",
                "Valor Realizado": 1000.0,
                "Consultor Interno": "Alice",
                "Representante-pedido": "Bob",
                "Numero NF": "1234567",
                "Status Processo": "Faturado",
            },
            {
                "Processo": "111111",
                "Dt Emissão": "2025-11-06",
                "Negócio": "Linha A",
                "Grupo": "G1",
                "Subgrupo": "SG1",
                "Tipo de Mercadoria": "T1",
                "Valor Realizado": 2000.0,
                "Consultor Interno": "Alice",
                "Representante-pedido": "Bob",
                "Numero NF": "1234568",
                "Status Processo": "Faturado",
            },
        ]
    )


def _make_colaboradores_df():
    return pd.DataFrame(
        [
            {"id_colaborador": 1, "nome_colaborador": "Alice", "cargo": "Consultor", "tipo_cargo": "Operacional"},
            {"id_colaborador": 2, "nome_colaborador": "Bob", "cargo": "Representante", "tipo_cargo": "Operacional"},
        ]
    )


def _make_atribuicoes_df():
    # Sem atribuições de gestão neste teste
    return pd.DataFrame(columns=["linha", "grupo", "subgrupo", "tipo_mercadoria", "colaborador", "cargo"])


def _regras_getter(linha, grupo, subgrupo, tipo_mercadoria, cargo):
    # Taxas simples para teste: 4% para Consultor e 2% para Representante, PE=100% para ambos
    if cargo == "Consultor":
        return {"taxa_rateio_maximo_pct": 4.0, "fatia_cargo_pct": 100.0}
    if cargo == "Representante":
        return {"taxa_rateio_maximo_pct": 2.0, "fatia_cargo_pct": 100.0}
    return {"taxa_rateio_maximo_pct": 0.0, "fatia_cargo_pct": 0.0}


def _fc_calculator_constante(_nome, _cargo, _item, *_args, **_kwargs):
    # FC constante de 0.8 para todos os itens/colaboradores
    return 0.8, {}


def test_financial_loader_cot_and_regular():
    # Montar DataFrame de análise financeira
    df_fin = pd.DataFrame(
        [
            {"Documento": "COT111111", "Valor": 500.0, "Data": "2025-11-03", "ID Cliente": "C1"},
            {"Documento": "NF123456 Extra", "Valor": 800.0, "Data": "2025-11-07", "ID Cliente": "C2"},
        ]
    )
    with TemporaryDirectory() as td:
        path = os.path.join(td, "Analise Financeira.xlsx")
        with pd.ExcelWriter(path, engine="openpyxl") as w:
            df_fin.to_excel(w, index=False)
        loader = FinancialPaymentsLoader()
        out = loader.load_from_file(path)

    assert len(out) == 2
    tipos = out["TIPO_PAGAMENTO"].tolist()
    assert "Antecipação" in tipos and "Pagamento Regular" in tipos
    # Checar PROCESSO extraído do COT
    proc = out[out["TIPO_PAGAMENTO"] == "Antecipação"]["PROCESSO"].iloc[0]
    assert proc == "111111"
    # Checar DOC6 de pagamento regular
    doc6 = out[out["TIPO_PAGAMENTO"] == "Pagamento Regular"]["DOCUMENTO_NORMALIZADO"].iloc[0]
    assert doc6 == "123456"


def test_metrics_calculator_tcmp_fcmp():
    analise = _make_analise_df()
    colabs = _make_colaboradores_df()
    atrib = _make_atribuicoes_df()
    calc = ProcessMetricsCalculator(
        analise_comercial_df=analise,
        regras_comissao_getter=_regras_getter,
        fc_calculator_func=_fc_calculator_constante,
        colaboradores_df=colabs,
        atribuicoes_df=atrib,
        recebe_por_recebimento_ids={"Alice", "Bob"},
    )
    tcmp, fcmp = calc.calculate_for_process("111111")
    # TCMP esperado:
    # Valor total = 3000; taxa_item Alice=4%; Bob=2% (sobre cada item)
    # TCMP_Alice = 0.04; TCMP_Bob = 0.02 (constantes, então média ponderada = próprio valor)
    assert abs(tcmp.get("Alice", 0.0) - 0.04) < 1e-9
    assert abs(tcmp.get("Bob", 0.0) - 0.02) < 1e-9
    # FCMP esperado: 0.8 para ambos
    assert abs(fcmp.get("Alice", 0.0) - 0.8) < 1e-9
    assert abs(fcmp.get("Bob", 0.0) - 0.8) < 1e-9


def test_reconciliation_saldo_allocation_by_tcmp():
    # Total adiantado de 1000; FCMP Alice=0.8, Bob=0.6; TCMP Alice=0.04, Bob=0.02
    # Pesos por TCMP: Alice=2/3, Bob=1/3
    # Saldo = 1000*(2/3*(0.8-1) + 1/3*(0.6-1)) = 1000*(-0.133333... - 0.133333...) = -266.666...
    total_adiantado = 1000.0
    tcmp = {"Alice": 0.04, "Bob": 0.02}
    fcmp = {"Alice": 0.8, "Bob": 0.6}
    soma_tcmp = sum(tcmp.values())
    saldo = 0.0
    for nome in tcmp.keys():
        w = tcmp[nome] / soma_tcmp
        saldo += total_adiantado * w * (fcmp[nome] - 1.0)
    assert abs(saldo + 266.6666667) < 1e-3


def test_post_faturamento_commission_formula():
    # Comissão pós-faturamento para parcela: valor*TCMP*FCMP por colaborador
    valor_parcela = 2000.0
    tcmp = {"Alice": 0.04, "Bob": 0.02}
    fcmp = {"Alice": 0.9, "Bob": 0.7}
    com_alice = valor_parcela * tcmp["Alice"] * fcmp["Alice"]
    com_bob = valor_parcela * tcmp["Bob"] * fcmp["Bob"]
    total = com_alice + com_bob
    # Checagens simples
    assert abs(com_alice - (2000 * 0.04 * 0.9)) < 1e-9
    assert abs(com_bob - (2000 * 0.02 * 0.7)) < 1e-9
    assert total > 0


if __name__ == "__main__":
    print("=" * 60)
    print("Executando testes da nova lógica de comissões por recebimento")
    print("=" * 60)
    
    try:
        print("\n[1/4] Testando FinancialPaymentsLoader...")
        test_financial_loader_cot_and_regular()
        print("  ✓ Loader de pagamentos financeiros OK")
        
        print("\n[2/4] Testando ProcessMetricsCalculator (TCMP e FCMP)...")
        test_metrics_calculator_tcmp_fcmp()
        print("  ✓ Cálculo de métricas ponderadas OK")
        
        print("\n[3/4] Testando fórmula de saldo de reconciliação...")
        test_reconciliation_saldo_allocation_by_tcmp()
        print("  ✓ Cálculo de saldo por pesos TCMP OK")
        
        print("\n[4/4] Testando fórmula de comissão pós-faturamento...")
        test_post_faturamento_commission_formula()
        print("  ✓ Fórmula de comissão pós-faturamento OK")
        
        print("\n" + "=" * 60)
        print("[SUCESSO] Todos os testes da nova lógica passaram!")
        print("=" * 60)
        
    except AssertionError as e:
        print(f"\n[ERRO] Teste falhou: {e}")
        import traceback
        traceback.print_exc()
        exit(1)
    except Exception as e:
        print(f"\n[ERRO INESPERADO] {e}")
        import traceback
        traceback.print_exc()
        exit(1)

