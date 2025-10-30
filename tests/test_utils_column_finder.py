"""
Testes para utils.column_finder
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
from utils.column_finder import ColumnFinder, find_column_simple


def test_column_finder_basic():
    """Testa busca básica de colunas."""
    df = pd.DataFrame(columns=['Valor Realizado', 'Consultor Interno', 'Processo'])
    finder = ColumnFinder(df)
    
    # Teste busca exata (case-insensitive)
    assert finder.find_column(['valor realizado']) == 'Valor Realizado'
    
    # Teste busca com múltiplos aliases
    assert finder.find_column(['valor_realizado', 'valor realizado', 'faturamento']) == 'Valor Realizado'
    
    # Teste coluna não encontrada
    assert finder.find_column(['coluna inexistente']) is None
    
    # Teste busca com espaços
    assert finder.find_column(['consultorinterno']) == 'Consultor Interno'
    
    print("[OK] test_column_finder_basic passou")


def test_column_finder_multiple():
    """Testa busca de múltiplas colunas."""
    df = pd.DataFrame(columns=['Processo', 'Valor Realizado', 'Consultor Interno'])
    finder = ColumnFinder(df)
    
    alias_groups = {
        'processo': ['processo', 'id processo'],
        'valor': ['valor realizado', 'faturamento'],
        'consultor': ['consultor interno', 'consultor']
    }
    
    results = finder.find_all_columns(alias_groups)
    
    assert results['processo'] == 'Processo'
    assert results['valor'] == 'Valor Realizado'
    assert results['consultor'] == 'Consultor Interno'
    
    print("[OK] test_column_finder_multiple passou")


def test_column_finder_helpers():
    """Testa métodos auxiliares."""
    df = pd.DataFrame(columns=['Valor Realizado', 'Processo'])
    finder = ColumnFinder(df)
    
    # Teste has_column
    assert finder.has_column(['valor realizado']) is True
    assert finder.has_column(['coluna inexistente']) is False
    
    # Teste get_column_or_default
    assert finder.get_column_or_default(['valor realizado']) == 'Valor Realizado'
    assert finder.get_column_or_default(['inexistente'], 'padrão') == 'padrão'
    
    print("[OK] test_column_finder_helpers passou")


def test_find_column_simple():
    """Testa função auxiliar find_column_simple."""
    df = pd.DataFrame(columns=['Processo', 'Valor Realizado'])
    
    assert find_column_simple(df, ['processo']) == 'Processo'
    assert find_column_simple(df, ['inexistente']) is None
    
    print("[OK] test_find_column_simple passou")


if __name__ == "__main__":
    print("Executando testes de ColumnFinder...")
    test_column_finder_basic()
    test_column_finder_multiple()
    test_column_finder_helpers()
    test_find_column_simple()
    print("\n[SUCESSO] Todos os testes de ColumnFinder passaram!")

