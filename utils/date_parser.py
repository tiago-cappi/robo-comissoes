"""
Utilitários para parsing robusto de datas.

Este módulo fornece funções para parsing de datas com detecção automática de
formato, tratamento de timestamps em nanosegundos, e outras situações comuns
encontradas nos dados do robô de comissões.
"""

import pandas as pd
from typing import Optional
from datetime import datetime
import re


def parse_date_smart(series: pd.Series) -> pd.Series:
    """
    Parse datas inteligentemente, detectando formato ISO automático.
    
    Esta função detecta se as datas estão em formato ISO (YYYY-MM-DD) ou em
    formato brasileiro (DD/MM/YYYY) e escolhe o parser apropriado.
    
    Args:
        series: Série do pandas com datas em formato string/misto
    
    Returns:
        Série com datas parseadas (tipo datetime64)
    
    Examples:
        >>> dates = pd.Series(['2025-01-15', '2025-02-20', '2025-03-10'])
        >>> parse_date_smart(dates)
        0   2025-01-15
        1   2025-02-20
        2   2025-03-10
        dtype: datetime64[ns]
    """
    # Converter para string e limpar
    raw = series.astype(str).str.strip().replace({'nan': ''})
    raw_clean = raw.str.replace('\u00a0', ' ', regex=False).str.replace('T', ' ', regex=False)
    
    # Verificar se a maioria está em formato ISO (YYYY-MM-DD)
    iso_pattern = r'^\d{4}-\d{2}-\d{2}'
    iso_count = raw_clean.str.match(iso_pattern, na=False).sum()
    
    # Se >= 50% são ISO format, usar yearfirst=True
    if iso_count >= max(1, int(0.5 * len(raw_clean))):
        return pd.to_datetime(raw_clean, yearfirst=True, errors='coerce')
    else:
        # Tentar ambos dayfirst e monthfirst, escolher o com menos NaT
        parsed1 = pd.to_datetime(raw_clean, dayfirst=True, errors='coerce')
        parsed2 = pd.to_datetime(raw_clean, dayfirst=False, errors='coerce')
        return parsed1 if parsed1.isna().sum() <= parsed2.isna().sum() else parsed2


def parse_date_column(df: pd.DataFrame, column_name: str, 
                      prefer_iso: Optional[bool] = None) -> pd.Series:
    """
    Parse coluna de datas em um DataFrame.
    
    Wrapper conveniente para parse_date_smart que opera diretamente
    em uma coluna de DataFrame.
    
    Args:
        df: DataFrame contendo a coluna
        column_name: Nome da coluna a ser parseada
        prefer_iso: Se True, força formato ISO; se False, força dayfirst;
                   se None (padrão), detecta automaticamente
    
    Returns:
        Série com datas parseadas
    
    Examples:
        >>> df = pd.DataFrame({'data': ['2025-01-15', '2025-02-20']})
        >>> parse_date_column(df, 'data')
        0   2025-01-15
        1   2025-02-20
        Name: data, dtype: datetime64[ns]
    """
    if column_name not in df.columns:
        raise ValueError(f"Coluna '{column_name}' não encontrada no DataFrame")
    
    if prefer_iso is None:
        return parse_date_smart(df[column_name])
    elif prefer_iso:
        return pd.to_datetime(df[column_name], yearfirst=True, errors='coerce')
    else:
        return pd.to_datetime(df[column_name], dayfirst=True, errors='coerce')


def detect_timestamp_nanoseconds(date_value) -> Optional[pd.Timestamp]:
    """
    Detecta e converte timestamps em nanosegundos para datetime.
    
    Algumas fontes de dados podem exportar datas como timestamps Unix em
    nanosegundos (números muito grandes). Esta função detecta esse padrão
    e converte apropriadamente.
    
    Args:
        date_value: Valor da data (pode ser string, número, etc.)
    
    Returns:
        pd.Timestamp se conseguiu converter, None caso contrário
    
    Examples:
        >>> # Timestamp em nanosegundos: 1706140800000000000 = 2024-01-25
        >>> detect_timestamp_nanoseconds('1706140800000000000')
        Timestamp('2024-01-25 00:00:00')
        >>> detect_timestamp_nanoseconds('2025-01-15')
        None  # não é timestamp em nanosegundos
    """
    try:
        date_str = str(date_value).strip()
        
        # Detectar timestamp em nanosegundos (número muito grande)
        if date_str.isdigit() and len(date_str) > 10:
            # Timestamps em nanosegundos têm ~19 dígitos
            # Timestamps em segundos têm ~10 dígitos
            return pd.to_datetime(int(date_str), unit='ns')
        
        return None
    except Exception:
        return None


def parse_date_flexible(date_value, dayfirst: bool = True) -> Optional[pd.Timestamp]:
    """
    Parse data com máxima flexibilidade, tentando múltiplas estratégias.
    
    Esta função tenta várias estratégias em sequência:
    1. Detectar timestamp em nanosegundos
    2. Parse com detecção de formato ISO
    3. Parse com dayfirst/yearfirst configurável
    4. Parse permissivo do pandas
    
    Args:
        date_value: Valor da data em qualquer formato
        dayfirst: Se True (padrão), assume formato DD/MM/YYYY quando ambíguo
    
    Returns:
        pd.Timestamp ou None se não conseguir parsear
    
    Examples:
        >>> parse_date_flexible('15/01/2025')
        Timestamp('2025-01-15 00:00:00')
        >>> parse_date_flexible('2025-01-15')
        Timestamp('2025-01-15 00:00:00')
        >>> parse_date_flexible('1706140800000000000')
        Timestamp('2024-01-25 00:00:00')
    """
    if pd.isna(date_value):
        return None
    
    try:
        date_str = str(date_value).strip()
        
        # Estratégia 1: Timestamp em nanosegundos
        ts_ns = detect_timestamp_nanoseconds(date_str)
        if ts_ns is not None:
            return ts_ns
        
        # Estratégia 2: Detectar formato ISO (YYYY-MM-DD)
        if len(date_str) >= 4 and date_str[:4].isdigit():
            result = pd.to_datetime(date_str, yearfirst=True, errors='coerce')
            if not pd.isna(result):
                return result
        
        # Estratégia 3: Usar dayfirst configurável
        result = pd.to_datetime(date_str, dayfirst=dayfirst, errors='coerce')
        if not pd.isna(result):
            return result
        
        # Estratégia 4: Último recurso - parse permissivo
        result = pd.to_datetime(date_str, errors='coerce')
        return result if not pd.isna(result) else None
        
    except Exception:
        return None


def extract_year_month(date_value) -> Optional[tuple]:
    """
    Extrai ano e mês de um valor de data.
    
    Args:
        date_value: Valor de data (pd.Timestamp, datetime, ou parseável)
    
    Returns:
        Tupla (ano, mes) ou None se não conseguir extrair
    
    Examples:
        >>> extract_year_month('2025-01-15')
        (2025, 1)
        >>> extract_year_month(pd.Timestamp('2025-03-20'))
        (2025, 3)
    """
    try:
        if isinstance(date_value, (pd.Timestamp, datetime)):
            return (date_value.year, date_value.month)
        
        parsed = parse_date_flexible(date_value)
        if parsed is not None:
            return (parsed.year, parsed.month)
        
        return None
    except Exception:
        return None

