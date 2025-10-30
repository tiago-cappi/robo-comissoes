"""
Testes para utils.date_parser
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
from datetime import datetime
from utils.date_parser import (
    parse_date_smart,
    parse_date_flexible,
    detect_timestamp_nanoseconds,
    extract_year_month
)


def test_parse_date_smart():
    """Testa parsing inteligente de datas."""
    # Teste com formato ISO
    dates_iso = pd.Series(['2025-01-15', '2025-02-20', '2025-03-10'])
    result = parse_date_smart(dates_iso)
    assert result.iloc[0] == pd.Timestamp('2025-01-15')
    assert not result.isna().any()
    
    # Teste com formato brasileiro
    dates_br = pd.Series(['15/01/2025', '20/02/2025', '10/03/2025'])
    result = parse_date_smart(dates_br)
    assert result.iloc[0] == pd.Timestamp('2025-01-15')
    
    print("[OK] test_parse_date_smart passou")


def test_parse_date_flexible():
    """Testa parsing flexível de datas."""
    # Formato ISO
    assert parse_date_flexible('2025-01-15') == pd.Timestamp('2025-01-15')
    
    # Formato brasileiro
    assert parse_date_flexible('15/01/2025') == pd.Timestamp('2025-01-15')
    
    # None
    assert parse_date_flexible(None) is None
    
    # String vazia
    result = parse_date_flexible('')
    assert result is None or pd.isna(result)
    
    print("[OK] test_parse_date_flexible passou")


def test_detect_timestamp_nanoseconds():
    """Testa detecção de timestamp em nanosegundos."""
    # Timestamp em nanosegundos (exemplo)
    # 1706140800000000000 = 2024-01-25 00:00:00 UTC
    ts_ns = '1706140800000000000'
    result = detect_timestamp_nanoseconds(ts_ns)
    assert result is not None
    assert isinstance(result, pd.Timestamp)
    
    # String normal (não é timestamp)
    result = detect_timestamp_nanoseconds('2025-01-15')
    assert result is None
    
    # Número pequeno (não é nanosegundos)
    result = detect_timestamp_nanoseconds('999999')
    assert result is None
    
    print("[OK] test_detect_timestamp_nanoseconds passou")


def test_extract_year_month():
    """Testa extração de ano e mês."""
    # String ISO
    assert extract_year_month('2025-01-15') == (2025, 1)
    
    # pd.Timestamp
    assert extract_year_month(pd.Timestamp('2025-03-20')) == (2025, 3)
    
    # datetime
    assert extract_year_month(datetime(2025, 5, 10)) == (2025, 5)
    
    # None
    assert extract_year_month(None) is None
    
    print("[OK] test_extract_year_month passou")


if __name__ == "__main__":
    print("Executando testes de date_parser...")
    test_parse_date_smart()
    test_parse_date_flexible()
    test_detect_timestamp_nanoseconds()
    test_extract_year_month()
    print("\n[SUCESSO] Todos os testes de date_parser passaram!")

