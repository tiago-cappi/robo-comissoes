"""
Testes para utils.normalization
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.normalization import normalize_text, normalize_process_id, normalize_column_name
import pandas as pd


def test_normalize_text():
    """Testa normalização de texto."""
    # Teste básico
    assert normalize_text("João Silva") == "JOAO SILVA"
    
    # Teste com espaços múltiplos
    assert normalize_text("  Gerente   Comercial  ") == "GERENTE COMERCIAL"
    
    # Teste com None
    assert normalize_text(None) == ""
    
    # Teste com NaN do pandas
    assert normalize_text(pd.NA) == ""
    
    # Teste com BOM
    assert normalize_text("\ufeffTexto") == "TEXTO"
    
    print("[OK] test_normalize_text passou")


def test_normalize_process_id():
    """Testa normalização de ID de processo."""
    # Teste com inteiro
    assert normalize_process_id(999999) == "999999"
    
    # Teste com float .0
    assert normalize_process_id(999999.0) == "999999"
    
    # Teste com string
    assert normalize_process_id("999999") == "999999"
    
    # Teste com espaços
    assert normalize_process_id("  123456  ") == "123456"
    
    # Teste com None
    assert normalize_process_id(None) is None
    
    # Teste com string vazia
    assert normalize_process_id("") is None
    
    # Teste com NaN
    assert normalize_process_id(float('nan')) is None
    
    print("[OK] test_normalize_process_id passou")


def test_normalize_column_name():
    """Testa normalização de nome de coluna."""
    # Teste básico
    assert normalize_column_name("Valor Realizado") == "valorrealizado"
    
    # Teste com espaços
    assert normalize_column_name("  Status Processo  ") == "statusprocesso"
    
    # Teste com BOM
    assert normalize_column_name("\ufeffProcesso") == "processo"
    
    # Teste com acentos
    assert normalize_column_name("Dt Emissão") == "dtemissao"
    
    print("[OK] test_normalize_column_name passou")


if __name__ == "__main__":
    print("Executando testes de normalização...")
    test_normalize_text()
    test_normalize_process_id()
    test_normalize_column_name()
    print("\n[SUCESSO] Todos os testes de normalizacao passaram!")

