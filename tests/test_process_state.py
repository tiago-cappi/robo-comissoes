"""
Testes para models.process_state
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
import tempfile
from models.process_state import ProcessStateManager, ESTADO_COLUMNS


def test_create_empty_state():
    """Testa criação de estado vazio."""
    manager = ProcessStateManager()
    
    assert manager.estado.shape[0] == 0  # vazio
    assert list(manager.estado.columns) == ESTADO_COLUMNS
    
    print("[OK] test_create_empty_state passou")


def test_process_doesnt_exist():
    """Testa verificação de processo inexistente."""
    manager = ProcessStateManager()
    
    assert not manager.process_exists(999999)
    assert manager.get_process_state(999999) is None
    
    print("[OK] test_process_doesnt_exist passou")


def test_update_payment_received_new_process():
    """Testa atualização de recebimento para processo novo."""
    manager = ProcessStateManager()
    
    # Criar novo processo
    manager.update_payment_received(
        processo_id=999999,
        valor_recebido=1000.0,
        valor_total_processo=5000.0,
        status_pagamento='Em Aberto'
    )
    
    # Verificar
    assert manager.process_exists(999999)
    state = manager.get_process_state(999999)
    assert state['TOTAL_PAGO_ACUMULADO'] == 1000.0
    assert state['VALOR_TOTAL_PROCESSO'] == 5000.0
    assert state['STATUS_PAGAMENTO'] == 'Em Aberto'
    assert state['STATUS_RECONCILIACAO'] == 'Nao Realizada'
    
    print("[OK] test_update_payment_received_new_process passou")


def test_update_payment_received_existing_process():
    """Testa atualização de recebimento para processo existente (incremento)."""
    manager = ProcessStateManager()
    
    # Criar processo
    manager.update_payment_received(999999, 1000.0, 5000.0)
    
    # Incrementar recebimento
    manager.update_payment_received(999999, 500.0)
    
    # Verificar incremento
    state = manager.get_process_state(999999)
    assert state['TOTAL_PAGO_ACUMULADO'] == 1500.0  # 1000 + 500
    
    print("[OK] test_update_payment_received_existing_process passou")


def test_update_commission_advanced():
    """Testa atualização de comissão adiantada."""
    manager = ProcessStateManager()
    
    # Criar com recebimento
    manager.update_payment_received(999999, 1000.0)
    
    # Adicionar comissão adiantada
    manager.update_commission_advanced(999999, 250.0)
    manager.update_commission_advanced(999999, 100.0)
    
    # Verificar
    state = manager.get_process_state(999999)
    assert state['TOTAL_ADIANTADO_COMISSAO'] == 350.0  # 250 + 100
    
    print("[OK] test_update_commission_advanced passou")


def test_update_process_status():
    """Testa atualização de status."""
    manager = ProcessStateManager()
    
    # Criar processo
    manager.update_payment_received(999999, 1000.0)
    
    # Atualizar status
    manager.update_process_status(
        999999,
        status_processo_analise='Faturado',
        status_pagamento='Quitado'
    )
    
    # Verificar
    state = manager.get_process_state(999999)
    assert state['STATUS_PROCESSO_ANALISE'] == 'Faturado'
    assert state['STATUS_PAGAMENTO'] == 'Quitado'
    
    print("[OK] test_update_process_status passou")


def test_mark_reconciliation_done():
    """Testa marcação de reconciliação concluída."""
    manager = ProcessStateManager()
    
    # Criar processo
    manager.update_payment_received(999999, 1000.0)
    
    # Marcar reconciliação
    manager.mark_reconciliation_done(999999)
    
    # Verificar
    state = manager.get_process_state(999999)
    assert state['STATUS_RECONCILIACAO'] == 'Realizada'
    
    print("[OK] test_mark_reconciliation_done passou")


def test_get_eligible_for_reconciliation():
    """Testa busca de processos elegíveis para reconciliação."""
    manager = ProcessStateManager()
    
    # Criar processo 1: elegível (quitado + faturado + não reconciliado)
    manager.update_payment_received(111111, 1000.0)
    manager.update_process_status(111111, 'Faturado', 'Quitado')
    
    # Criar processo 2: não elegível (não quitado)
    manager.update_payment_received(222222, 1000.0)
    manager.update_process_status(222222, 'Faturado', 'Em Aberto')
    
    # Criar processo 3: não elegível (já reconciliado)
    manager.update_payment_received(333333, 1000.0)
    manager.update_process_status(333333, 'Faturado', 'Quitado')
    manager.mark_reconciliation_done(333333)
    
    # Buscar elegíveis
    eligible = manager.get_eligible_for_reconciliation()
    
    # Deve retornar apenas processo 111111
    assert len(eligible) == 1
    assert eligible.iloc[0]['PROCESSO'] == '111111'
    
    print("[OK] test_get_eligible_for_reconciliation passou")


def test_save_and_load():
    """Testa salvar e carregar de arquivo."""
    manager = ProcessStateManager()
    
    # Adicionar alguns processos
    manager.update_payment_received(111111, 1000.0, 5000.0, 'Quitado')
    manager.update_payment_received(222222, 2000.0, 8000.0, 'Em Aberto')
    
    # Salvar em arquivo temporário
    with tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False) as tmp:
        tmp_path = tmp.name
    
    try:
        # Salvar
        success = manager.save_to_file(tmp_path)
        assert success
        
        # Carregar em novo manager
        manager2 = ProcessStateManager(filepath=tmp_path)
        success = manager2.load_from_file()
        assert success
        
        # Verificar que carregou corretamente
        assert len(manager2.estado) == 2
        assert manager2.process_exists(111111)
        assert manager2.process_exists(222222)
        
        state1 = manager2.get_process_state(111111)
        assert state1['TOTAL_PAGO_ACUMULADO'] == 1000.0
        assert state1['STATUS_PAGAMENTO'] == 'Quitado'
        
    finally:
        # Limpar arquivo temporário
        if os.path.exists(tmp_path):
            os.remove(tmp_path)
    
    print("[OK] test_save_and_load passou")


def test_get_process_summary():
    """Testa resumo estatístico."""
    manager = ProcessStateManager()
    
    # Estado vazio
    summary = manager.get_process_summary()
    assert summary['total_processos'] == 0
    assert summary['total_pago'] == 0.0
    
    # Adicionar processos
    manager.update_payment_received(111111, 1000.0)
    manager.update_commission_advanced(111111, 250.0)
    manager.update_process_status(111111, 'Faturado', 'Quitado')
    
    manager.update_payment_received(222222, 2000.0)
    manager.update_commission_advanced(222222, 500.0)
    manager.update_process_status(222222, 'Faturado', 'Quitado')
    manager.mark_reconciliation_done(222222)
    
    # Verificar resumo
    summary = manager.get_process_summary()
    assert summary['total_processos'] == 2
    assert summary['total_pago'] == 3000.0  # 1000 + 2000
    assert summary['total_adiantado'] == 750.0  # 250 + 500
    assert summary['processos_quitados'] == 2
    assert summary['processos_reconciliados'] == 1
    assert summary['processos_elegiveis_reconciliacao'] == 1  # apenas 111111
    
    print("[OK] test_get_process_summary passou")


if __name__ == "__main__":
    print("Executando testes de ProcessStateManager...")
    test_create_empty_state()
    test_process_doesnt_exist()
    test_update_payment_received_new_process()
    test_update_payment_received_existing_process()
    test_update_commission_advanced()
    test_update_process_status()
    test_mark_reconciliation_done()
    test_get_eligible_for_reconciliation()
    test_save_and_load()
    test_get_process_summary()
    print("\n[SUCESSO] Todos os testes de ProcessStateManager passaram!")

