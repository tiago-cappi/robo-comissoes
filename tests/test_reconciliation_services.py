"""
Testes para os serviços de reconciliação.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
import tempfile
from services.historical_data_loader import HistoricalDataLoader
from services.realized_metrics_builder import RealizedMetricsBuilder
from services.reconciliation_calculator import ReconciliationCalculator
from services.reconciliation_processor import ReconciliationProcessor
from models.process_state import ProcessStateManager


# === Testes do HistoricalDataLoader ===

def test_historical_loader_availability():
    """Testa verificação de disponibilidade de dados."""
    loader = HistoricalDataLoader()
    
    # Verificar disponibilidade (não falha mesmo se arquivos não existem)
    availability = loader.check_data_availability(1, 2025)
    
    assert isinstance(availability, dict)
    assert 'rentabilidade' in availability
    assert 'faturados' in availability
    assert isinstance(availability['rentabilidade'], bool)
    
    print("[OK] test_historical_loader_availability passou")


def test_historical_loader_available_months():
    """Testa listagem de meses disponíveis."""
    loader = HistoricalDataLoader()
    
    # Listar meses (retorna lista vazia se pasta não existe)
    available = loader.get_available_months()
    
    assert isinstance(available, list)
    # Cada item deve ser tupla (mes, ano)
    for item in available:
        assert isinstance(item, tuple)
        assert len(item) == 2
        assert 1 <= item[0] <= 12  # mês válido
        assert 2000 <= item[1] <= 2100  # ano razoável
    
    print("[OK] test_historical_loader_available_months passou")


# === Testes do RealizedMetricsBuilder ===

def test_metrics_builder_empty():
    """Testa construção de métricas com DataFrames vazios."""
    builder = RealizedMetricsBuilder()
    
    series = builder.build_from_dataframes(
        pd.DataFrame(),
        pd.DataFrame(),
        pd.DataFrame()
    )
    
    # Deve retornar dicionário com todas as chaves
    assert 'faturamento_linha' in series
    assert 'faturamento_individual' in series
    assert 'conversao_linha' in series
    assert 'conversao_individual' in series
    assert 'rentabilidade' in series
    
    # Todas devem ser Series (vazias)
    for key, value in series.items():
        assert isinstance(value, pd.Series)
        assert value.empty
    
    print("[OK] test_metrics_builder_empty passou")


def test_metrics_builder_with_data():
    """Testa construção de métricas com dados reais."""
    builder = RealizedMetricsBuilder()
    
    # Dados de faturamento
    faturados_df = pd.DataFrame({
        'Negócio': ['Linha A', 'Linha A', 'Linha B'],
        'Consultor Interno': ['João', 'Maria', 'João'],
        'Valor Realizado': [1000.0, 1500.0, 2000.0]
    })
    
    # Dados de conversão
    conversoes_df = pd.DataFrame({
        'Negócio': ['Linha A', 'Linha B'],
        'Consultor Interno': ['João', 'Maria'],
        'Valor Orçado': [500.0, 800.0]
    })
    
    # Dados de rentabilidade
    rentabilidade_df = pd.DataFrame({
        'Negócio': ['Linha A', 'Linha B'],
        'Grupo': ['Grupo 1', 'Grupo 2'],
        'Subgrupo': ['Sub 1', 'Sub 2'],
        'Tipo de Mercadoria': ['Tipo X', 'Tipo Y'],
        'rentabilidade_realizada_pct': [15.5, 20.3]
    })
    
    series = builder.build_from_dataframes(faturados_df, conversoes_df, rentabilidade_df)
    
    # Verificar faturamento por linha
    assert not series['faturamento_linha'].empty
    assert series['faturamento_linha']['Linha A'] == 2500.0  # 1000 + 1500
    assert series['faturamento_linha']['Linha B'] == 2000.0
    
    # Verificar faturamento individual
    assert series['faturamento_individual']['João'] == 3000.0  # 1000 + 2000
    assert series['faturamento_individual']['Maria'] == 1500.0
    
    # Verificar conversão por linha
    assert series['conversao_linha']['Linha A'] == 500.0
    assert series['conversao_linha']['Linha B'] == 800.0
    
    # Verificar rentabilidade (multi-índice)
    assert not series['rentabilidade'].empty
    assert len(series['rentabilidade']) == 2
    
    print("[OK] test_metrics_builder_with_data passou")


def test_metrics_builder_validation():
    """Testa validação de séries construídas."""
    builder = RealizedMetricsBuilder()
    
    faturados_df = pd.DataFrame({
        'Negócio': ['Linha A'],
        'Valor Realizado': [1000.0]
    })
    
    series = builder.build_from_dataframes(faturados_df, pd.DataFrame(), pd.DataFrame())
    
    # Validar
    stats = builder.validate_series(series)
    
    assert isinstance(stats, dict)
    assert 'faturamento_linha' in stats
    assert stats['faturamento_linha']['valid'] is True
    assert stats['faturamento_linha']['count'] == 1
    assert stats['faturamento_linha']['total'] == 1000.0
    
    print("[OK] test_metrics_builder_validation passou")


# === Testes do ReconciliationCalculator ===

def test_reconciliation_calculator_no_process():
    """Testa cálculo com processo inexistente."""
    analise_df = pd.DataFrame({
        'Processo': ['999999'],
        'Valor Realizado': [5000.0]
    })
    
    # Mock de funções
    def mock_fc(*args, **kwargs):
        return {'fc_final': 1.0}
    
    def mock_regra(*args):
        return {'taxa_rateio_maximo_pct': 2.0, 'fatia_cargo_pct': 50.0}
    
    calculator = ReconciliationCalculator(
        analise_df,
        mock_fc,
        mock_regra,
        pd.DataFrame(),
        pd.DataFrame(),
        set()
    )
    
    # Processo inexistente
    linhas, total = calculator.reconcile_process('111111')
    
    assert len(linhas) == 0
    assert total == 0.0
    
    print("[OK] test_reconciliation_calculator_no_process passou")


# === Testes do ReconciliationProcessor ===

def test_reconciliation_processor_no_eligible():
    """Testa processador sem processos elegíveis."""
    state_manager = ProcessStateManager()
    
    # Mock de calculator
    class MockCalculator:
        def reconcile_process(self, proc_id):
            return [], 0.0
    
    processor = ReconciliationProcessor(state_manager, MockCalculator())
    
    # Processar (não há elegíveis)
    det_df, res_df = processor.process_all_eligible()
    
    assert det_df.empty
    assert res_df.empty
    
    print("[OK] test_reconciliation_processor_no_eligible passou")


def test_reconciliation_processor_with_eligible():
    """Testa processador com processos elegíveis."""
    state_manager = ProcessStateManager()
    
    # Criar processo elegível
    state_manager.update_payment_received(999999, 1000.0)
    state_manager.update_commission_advanced(999999, 250.0)
    state_manager.update_process_status(999999, 'Faturado', 'Quitado')
    
    # Mock de calculator
    class MockCalculator:
        def reconcile_process(self, proc_id):
            # Simular comissão correta de R$ 300
            return [
                {'processo': proc_id, 'comissao_calculada': 150.0},
                {'processo': proc_id, 'comissao_calculada': 150.0}
            ], 300.0
    
    processor = ReconciliationProcessor(state_manager, MockCalculator())
    
    # Processar
    det_df, res_df = processor.process_all_eligible()
    
    # Verificações
    assert not det_df.empty
    assert len(det_df) == 2
    assert not res_df.empty
    assert len(res_df) == 1
    
    # Verificar resumo
    assert res_df.iloc[0]['PROCESSO'] == '999999'
    assert res_df.iloc[0]['COMISSAO_CORRETA_TOTAL'] == 300.0
    assert res_df.iloc[0]['TOTAL_ADIANTAMENTOS_PAGOS'] == 250.0
    assert res_df.iloc[0]['SALDO_FINAL_RECONCILIACAO'] == 50.0  # 300 - 250
    
    # Verificar que foi marcado como reconciliado
    state = state_manager.get_process_state(999999)
    assert state['STATUS_RECONCILIACAO'] == 'Realizada'
    
    print("[OK] test_reconciliation_processor_with_eligible passou")


def test_reconciliation_processor_summary():
    """Testa geração de resumo."""
    state_manager = ProcessStateManager()
    
    # Criar dois processos
    state_manager.update_payment_received(111111, 1000.0)
    state_manager.update_commission_advanced(111111, 100.0)
    state_manager.update_process_status(111111, 'Faturado', 'Quitado')
    
    state_manager.update_payment_received(222222, 2000.0)
    state_manager.update_commission_advanced(222222, 300.0)
    state_manager.update_process_status(222222, 'Faturado', 'Quitado')
    
    # Mock calculator
    class MockCalculator:
        def reconcile_process(self, proc_id):
            # 111111: correto=150, adiantado=100 -> saldo +50
            # 222222: correto=250, adiantado=300 -> saldo -50
            if proc_id == '111111':
                return [{'comissao_calculada': 150.0}], 150.0
            else:
                return [{'comissao_calculada': 250.0}], 250.0
    
    processor = ReconciliationProcessor(state_manager, MockCalculator())
    
    # Processar
    det_df, res_df = processor.process_all_eligible()
    
    # Gerar resumo
    summary = processor.get_processing_summary(res_df)
    
    assert summary['total_processos'] == 2
    assert summary['comissao_correta_total'] == 400.0  # 150 + 250
    assert summary['adiantamentos_pagos_total'] == 400.0  # 100 + 300
    assert summary['saldo_final_total'] == 0.0  # +50 - 50
    assert summary['processos_com_saldo_positivo'] == 1
    assert summary['processos_com_saldo_negativo'] == 1
    assert summary['processos_com_saldo_zero'] == 0
    
    print("[OK] test_reconciliation_processor_summary passou")


def test_reconciliation_processor_requiring_payment():
    """Testa identificação de processos que requerem pagamento."""
    # Criar resumo mock
    resumo_df = pd.DataFrame({
        'PROCESSO': ['111111', '222222', '333333'],
        'COMISSAO_CORRETA_TOTAL': [150.0, 250.0, 100.0],
        'TOTAL_ADIANTAMENTOS_PAGOS': [100.0, 300.0, 100.0],
        'SALDO_FINAL_RECONCILIACAO': [50.0, -50.0, 0.0]
    })
    
    processor = ReconciliationProcessor(None, None)
    
    # Processos que requerem pagamento (saldo positivo)
    requiring = processor.get_processes_requiring_payment(resumo_df)
    
    assert len(requiring) == 1
    assert requiring.iloc[0]['PROCESSO'] == '111111'
    assert requiring.iloc[0]['SALDO_FINAL_RECONCILIACAO'] == 50.0
    
    # Processos com pagamento excessivo (saldo negativo)
    overpaid = processor.get_processes_with_overpayment(resumo_df)
    
    assert len(overpaid) == 1
    assert overpaid.iloc[0]['PROCESSO'] == '222222'
    assert overpaid.iloc[0]['SALDO_FINAL_RECONCILIACAO'] == -50.0
    
    print("[OK] test_reconciliation_processor_requiring_payment passou")


if __name__ == "__main__":
    print("Executando testes dos serviços de reconciliação...")
    
    # HistoricalDataLoader
    test_historical_loader_availability()
    test_historical_loader_available_months()
    
    # RealizedMetricsBuilder
    test_metrics_builder_empty()
    test_metrics_builder_with_data()
    test_metrics_builder_validation()
    
    # ReconciliationCalculator
    test_reconciliation_calculator_no_process()
    
    # ReconciliationProcessor
    test_reconciliation_processor_no_eligible()
    test_reconciliation_processor_with_eligible()
    test_reconciliation_processor_summary()
    test_reconciliation_processor_requiring_payment()
    
    print("\n[SUCESSO] Todos os testes dos serviços de reconciliação passaram!")

