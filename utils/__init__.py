"""
Módulo de utilitários para o robô de comissões.

Este pacote contém funções auxiliares reutilizáveis para:
- Normalização de textos e processos
- Busca de colunas em DataFrames
- Parsing de datas
"""

from .normalization import (
    normalize_text,
    normalize_process_id,
    normalize_column_name
)

from .column_finder import ColumnFinder

from .date_parser import (
    parse_date_column,
    parse_date_smart,
    detect_timestamp_nanoseconds
)

__all__ = [
    'normalize_text',
    'normalize_process_id',
    'normalize_column_name',
    'ColumnFinder',
    'parse_date_column',
    'parse_date_smart',
    'detect_timestamp_nanoseconds'
]

