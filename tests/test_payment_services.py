"""
Testes para os serviços de processamento de recebimentos.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
from services.payment_mapper import PaymentMapper
from services.payment_commission_calculator import PaymentCommissionCalculator
from services.payment_processor import PaymentProcessor
from models.process_state import ProcessStateManager


# === Testes do PaymentMapper ===

def test_payment_mapper_exact_match():
    """Testa mapeamento exato de processo."""
    # Criar DataFrame de análise
    analise_df = pd.DataFrame({
        'Processo': ['999999', '888888', '777777'],
        'Negócio': ['Linha A', 'Linha B', 'Linha C'],
        'Valor Realizado': [5000.0, 3000.0, 2000.0]
    })
    
    mapper = PaymentMapper(analise_df)
    
    # Teste com match exato
    row, method = mapper.map_payment(999999, 1000.0)
    
    assert row is not None
    assert method == 'exact_match'
    assert row['Processo'] == '999999'
    assert row['Negócio'] == 'Linha A'
    
    print("[OK] test_payment_mapper_exact_match passou")


def test_payment_mapper_not_found():
    """Testa processo não encontrado."""
    analise_df = pd.DataFrame({
        'Processo': ['999999', '888888'],
        'Valor Realizado': [5000.0, 3000.0]
    })
    
    mapper = PaymentMapper(analise_df)
    
    # Teste com processo inexistente
    row, method = mapper.map_payment(111111, 1000.0)
    
    assert row is None
    assert method == 'not_found'
    
    print("[OK] test_payment_mapper_not_found passou")


def test_payment_mapper_substring_match():
    """Testa mapeamento por substring."""
    analise_df = pd.DataFrame({
        'Processo': ['999999-A', '888888-B', '777777-C'],
        'Valor Realizado': [5000.0, 3000.0, 2000.0]
    })
    
    mapper = PaymentMapper(analise_df)
    
    # Teste com substring (processo '999999' deve encontrar '999999-A')
    row, method = mapper.map_payment('999999', 1000.0)
    
    assert row is not None
    assert method in ('substring_match', 'substring_match_with_value')
    assert '999999' in row['Processo']
    
    print("[OK] test_payment_mapper_substring_match passou")


def test_payment_mapper_get_context():
    """Testa extração de contexto do processo."""
    analise_df = pd.DataFrame({
        'Processo': ['999999'],
        'Negócio': ['Linha A'],
        'Grupo': ['Grupo 1'],
        'Subgrupo': ['Sub 1'],
        'Tipo de Mercadoria': ['Tipo X'],
        'Cliente': ['Cliente ABC'],
        'Valor Realizado': [5000.0]
    })
    
    mapper = PaymentMapper(analise_df)
    row, _ = mapper.map_payment(999999)
    
    context = mapper.get_process_context(row)
    
    assert context['processo'] == '999999'
    assert context['linha'] == 'Linha A'
    assert context['grupo'] == 'Grupo 1'
    assert context['subgrupo'] == 'Sub 1'
    assert context['tipo_mercadoria'] == 'Tipo X'
    assert context['cliente'] == 'Cliente ABC'
    assert context['valor_processo'] == 5000.0
    
    print("[OK] test_payment_mapper_get_context passou")


# === Testes do PaymentCommissionCalculator ===

def test_payment_commission_calculator_basic():
    """Testa cálculo básico de comissão por recebimento."""
    # Setup
    colaboradores_df = pd.DataFrame({
        'id_colaborador': [1, 2, 3],
        'nome_colaborador': ['João Silva', 'Maria Santos', 'Pedro Costa'],
        'cargo': ['Gerente Comercial', 'Consultor', 'Gerente Linha'],
        'tipo_cargo': ['Gestão', 'Operacional', 'Gestão']
    })
    
    atribuicoes_df = pd.DataFrame({
        'colaborador': ['João Silva'],
        'cargo': ['Gerente Comercial'],
        'linha': ['Linha A'],
        'grupo': ['Grupo 1'],
        'subgrupo': ['Sub 1'],
        'tipo_mercadoria': ['Tipo X']
    })
    
    recebe_por_recebimento = {'João Silva', 'Maria Santos'}
    
    # Mock de regras de comissão
    def mock_regra(linha, grupo, subgrupo, tipo, cargo):
        return {
            'taxa_rateio_maximo_pct': 2.0,  # 2%
            'fatia_cargo_pct': 50.0  # 50%
        }
    
    calculator = PaymentCommissionCalculator(
        mock_regra,
        colaboradores_df,
        atribuicoes_df,
        recebe_por_recebimento
    )
    
    # Testar cálculo
    process_context = {
        'linha': 'Linha A',
        'grupo': 'Grupo 1',
        'subgrupo': 'Sub 1',
        'tipo_mercadoria': 'Tipo X',
        'consultor_interno': 'Maria Santos',
        'representante': None
    }
    
    comissoes = calculator.calculate_for_payment(
        '999999',
        10000.0,  # R$ 10.000,00 recebidos
        process_context
    )
    
    # Deve gerar comissões para João (gestão) e Maria (operacional)
    assert len(comissoes) == 2
    
    # Verificar comissão: 10000 * 0.02 * 0.50 = 100.00
    for com in comissoes:
        assert com['comissao_calculada'] == 100.0
        assert com['fator_correcao_fc'] == 1.0
        assert com['tipo_lancamento'] == 'Recebimento'
    
    print("[OK] test_payment_commission_calculator_basic passou")


def test_payment_commission_calculator_is_receiver():
    """Testa verificação de quem recebe por recebimento."""
    colaboradores_df = pd.DataFrame({
        'nome_colaborador': ['João Silva', 'Maria Santos'],
        'cargo': ['Gerente', 'Consultor']
    })
    
    recebe_por_recebimento = {'João Silva'}
    
    calculator = PaymentCommissionCalculator(
        lambda *args: {},
        colaboradores_df,
        pd.DataFrame(),
        recebe_por_recebimento
    )
    
    assert calculator.is_payment_receiver('João Silva') is True
    assert calculator.is_payment_receiver('joao silva') is True  # case-insensitive
    assert calculator.is_payment_receiver('Maria Santos') is False
    
    print("[OK] test_payment_commission_calculator_is_receiver passou")


# === Testes do PaymentProcessor ===

def test_payment_processor_full_flow():
    """Testa fluxo completo de processamento de recebimentos."""
    # Dados de análise comercial
    analise_df = pd.DataFrame({
        'Processo': ['999999', '888888'],
        'Negócio': ['Linha A', 'Linha B'],
        'Grupo': ['Grupo 1', 'Grupo 2'],
        'Subgrupo': ['Sub 1', 'Sub 2'],
        'Tipo de Mercadoria': ['Tipo X', 'Tipo Y'],
        'Consultor Interno': ['João Silva', 'Maria Santos'],
        'Valor Realizado': [5000.0, 3000.0]
    })
    
    # Dados de recebimentos
    recebimentos_df = pd.DataFrame({
        'PROCESSO': [999999, 888888, 111111],  # 111111 não existe
        'VALOR_RECEBIDO': [1000.0, 500.0, 300.0],
        'ID_CLIENTE': [1, 2, 3]
    })
    
    # Colaboradores
    colaboradores_df = pd.DataFrame({
        'id_colaborador': [1, 2],
        'nome_colaborador': ['João Silva', 'Maria Santos'],
        'cargo': ['Consultor', 'Consultor'],
        'tipo_cargo': ['Operacional', 'Operacional']
    })
    
    # Regras de comissão mock
    def mock_regra(*args):
        return {'taxa_rateio_maximo_pct': 2.0, 'fatia_cargo_pct': 50.0}
    
    # Calculator
    calculator = PaymentCommissionCalculator(
        mock_regra,
        colaboradores_df,
        pd.DataFrame(),
        {'João Silva', 'Maria Santos'}
    )
    
    # State manager
    state_manager = ProcessStateManager()
    
    # Processor
    processor = PaymentProcessor(
        recebimentos_df,
        analise_df,
        calculator,
        state_manager
    )
    
    # Processar
    comissoes_df, log_map = processor.process_all_payments()
    
    # Verificações
    assert len(log_map) == 3  # 3 recebimentos processados
    
    # Dois devem ser mapeados
    mapeados = [log for log in log_map if log['status'] == 'MAPEADO']
    assert len(mapeados) == 2
    
    # Um não mapeado
    nao_mapeados = [log for log in log_map if log['status'] == 'NAO_MAPEADO']
    assert len(nao_mapeados) == 1
    
    # Resumo
    summary = processor.get_processing_summary(log_map)
    assert summary['total_recebimentos'] == 3
    assert summary['mapeados'] == 2
    assert summary['nao_mapeados'] == 1
    assert summary['taxa_mapeamento'] == pytest.approx(66.67, rel=0.1)
    
    # Estado deve ter sido atualizado
    assert state_manager.process_exists(999999)
    assert state_manager.process_exists(888888)
    
    state_999 = state_manager.get_process_state(999999)
    assert state_999['TOTAL_PAGO_ACUMULADO'] == 1000.0
    
    print("[OK] test_payment_processor_full_flow passou")


def test_payment_processor_no_state_manager():
    """Testa processador sem state manager (sem atualizar estado)."""
    analise_df = pd.DataFrame({
        'Processo': ['999999'],
        'Valor Realizado': [5000.0]
    })
    
    recebimentos_df = pd.DataFrame({
        'PROCESSO': [999999],
        'VALOR_RECEBIDO': [1000.0]
    })
    
    colaboradores_df = pd.DataFrame({
        'nome_colaborador': ['João'],
        'cargo': ['Consultor'],
        'id_colaborador': [1]
    })
    
    calculator = PaymentCommissionCalculator(
        lambda *args: {'taxa_rateio_maximo_pct': 2.0, 'fatia_cargo_pct': 50.0},
        colaboradores_df,
        pd.DataFrame(),
        set()
    )
    
    # Sem state_manager
    processor = PaymentProcessor(
        recebimentos_df,
        analise_df,
        calculator,
        state_manager=None
    )
    
    comissoes_df, log_map = processor.process_all_payments()
    
    # Deve funcionar normalmente, apenas não atualiza estado
    assert len(log_map) == 1
    
    print("[OK] test_payment_processor_no_state_manager passou")


# Mock simples de pytest.approx (caso não tenha pytest instalado)
class _Approx:
    def __init__(self, value, rel=1e-6):
        self.value = value
        self.rel = rel
    
    def __eq__(self, other):
        return abs(self.value - other) <= abs(self.value * self.rel)

# Criar namespace pytest se não existir
class _Pytest:
    approx = _Approx

pytest = _Pytest()


if __name__ == "__main__":
    print("Executando testes dos serviços de recebimento...")
    
    # PaymentMapper
    test_payment_mapper_exact_match()
    test_payment_mapper_not_found()
    test_payment_mapper_substring_match()
    test_payment_mapper_get_context()
    
    # PaymentCommissionCalculator
    test_payment_commission_calculator_basic()
    test_payment_commission_calculator_is_receiver()
    
    # PaymentProcessor
    test_payment_processor_full_flow()
    test_payment_processor_no_state_manager()
    
    print("\n[SUCESSO] Todos os testes dos serviços de recebimento passaram!")

