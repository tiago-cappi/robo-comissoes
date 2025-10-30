"""
Utilitários para normalização de textos, processos e colunas.

Este módulo centraliza toda a lógica de normalização usada no robô de comissões,
eliminando duplicação de código e garantindo consistência.
"""

import unicodedata
import pandas as pd
import numpy as np
from typing import Optional


def normalize_text(s) -> str:
    """
    Normaliza texto para comparação (remove acentos, BOM, uppercase, trim).
    
    Esta função é usada para comparações case-insensitive e accent-insensitive
    em todo o robô (nomes de colaboradores, cargos, status, etc).
    
    Args:
        s: Texto a ser normalizado (pode ser None, str, ou qualquer tipo conversível)
    
    Returns:
        String normalizada (vazia se input for None/NaN)
    
    Examples:
        >>> normalize_text("João Silva")
        "JOAO SILVA"
        >>> normalize_text("  Gerente   Comercial  ")
        "GERENTE COMERCIAL"
        >>> normalize_text(None)
        ""
    """
    if pd.isna(s):
        return ""
    s = str(s)
    # Remover BOM (Byte Order Mark) se presente
    s = s.replace('\ufeff', '')
    # Normalizar Unicode (remover acentos)
    s = unicodedata.normalize("NFKD", s).encode("ASCII", "ignore").decode("ASCII")
    # Uppercase, trim e normalizar espaços múltiplos
    return " ".join(s.strip().upper().split())


def normalize_process_id(val) -> Optional[str]:
    """
    Normaliza ID de processo para comparação consistente.
    
    Esta função trata processos que podem vir como int, float, string, etc.,
    e garante uma representação consistente para comparação. Converte floats
    com parte decimal zero (ex: 999999.0) para inteiro (999999).
    
    Args:
        val: ID do processo (int, float, str, ou None)
    
    Returns:
        String normalizada do processo, ou None se inválido/vazio
    
    Examples:
        >>> normalize_process_id(999999)
        "999999"
        >>> normalize_process_id(999999.0)
        "999999"
        >>> normalize_process_id("999999")
        "999999"
        >>> normalize_process_id("  123456  ")
        "123456"
        >>> normalize_process_id(None)
        None
        >>> normalize_process_id("")
        None
    """
    # Tratar None e NaN
    if val is None or (isinstance(val, float) and pd.isna(val)):
        return None
    
    # Tratar inteiros
    if isinstance(val, (int, np.integer)):
        return str(int(val))
    
    # Tratar floats
    if isinstance(val, float):
        if pd.isna(val):
            return None
        if float(val).is_integer():
            return str(int(val))
        return str(val).strip()
    
    # Tratar strings
    s = str(val).strip()
    if not s:
        return None
    
    # Tentar converter para número e normalizar
    try:
        s_float = float(s.replace(',', '.'))
        if float(s_float).is_integer():
            return str(int(s_float))
    except Exception:
        pass
    
    return s


def normalize_column_name(col: str) -> str:
    """
    Normaliza nome de coluna para busca (remove BOM, espaços, lowercase).
    
    Esta função é usada para comparar nomes de colunas em DataFrames,
    permitindo busca tolerante a diferenças de formatação.
    
    Args:
        col: Nome da coluna
    
    Returns:
        Nome normalizado (lowercase, sem BOM, sem espaços extras)
    
    Examples:
        >>> normalize_column_name("  Valor Realizado  ")
        "valorrealizado"
        >>> normalize_column_name("﻿Status Processo")  # com BOM
        "statusprocesso"
        >>> normalize_column_name("Dt Emissão")
        "dtemissao"
    """
    if pd.isna(col):
        return ""
    
    s = str(col).strip()
    # Remover BOM
    s = s.replace('\ufeff', '')
    # Normalizar Unicode (remover acentos)
    s = unicodedata.normalize("NFKD", s).encode("ASCII", "ignore").decode("ASCII")
    # Lowercase e remover todos os espaços
    s = s.lower().replace(' ', '')
    
    return s


def normalize_for_fuzzy_match(s: str) -> str:
    """
    Normaliza texto para matching fuzzy/aproximado.
    
    Similar a normalize_text, mas mantém lowercase (mais adequado para 
    comparações fuzzy) e remove mais caracteres especiais.
    
    Args:
        s: Texto a normalizar
    
    Returns:
        Texto normalizado para matching fuzzy
    
    Examples:
        >>> normalize_for_fuzzy_match("João da Silva-Júnior")
        "joao da silva junior"
    """
    if pd.isna(s):
        return ""
    
    s = str(s)
    # Remover BOM
    s = s.replace('\ufeff', '')
    # Normalizar Unicode
    s = unicodedata.normalize("NFKD", s).encode("ASCII", "ignore").decode("ASCII")
    # Remover caracteres especiais comuns
    s = s.replace('-', ' ').replace('_', ' ').replace('.', ' ')
    # Lowercase, trim e normalizar espaços
    return " ".join(s.strip().lower().split())

