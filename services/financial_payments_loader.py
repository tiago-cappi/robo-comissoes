"""
Carregamento de pagamentos a partir de 'Análise Financeira.xlsx'.

Regras:
- Se 'Documento' começar com 'COT' (case-insensitive) => TIPO_PAGAMENTO='Antecipação'
  e 'PROCESSO' = sufixo após 'COT' (apenas dígitos)
- Caso contrário => TIPO_PAGAMENTO='Pagamento Regular' e
  'DOCUMENTO_NORMALIZADO' = 6 primeiros dígitos em 'Documento'

Saída: DataFrame unificado com colunas padronizadas:
- TIPO_PAGAMENTO ('Antecipação' | 'Pagamento Regular')
- PROCESSO (somente para 'Antecipação')
- DOCUMENTO_ORIGINAL
- DOCUMENTO_NORMALIZADO (somente para 'Pagamento Regular')
- VALOR_PAGO
- DATA_PAGAMENTO
- ID_CLIENTE
"""

import os
import sys
import pandas as pd
from typing import Optional

# Adicionar path para imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.column_finder import ColumnFinder


class FinancialPaymentsLoader:
    """Responsável por ler e normalizar pagamentos da Análise Financeira."""

    def __init__(self):
        pass

    def load_from_file(self, filepath: str) -> pd.DataFrame:
        """
        Lê e normaliza o arquivo 'Análise Financeira.xlsx'.

        Args:
            filepath: Caminho para o arquivo

        Returns:
            DataFrame com colunas padronizadas (ver docstring do módulo)
        """
        if not filepath or not os.path.exists(filepath):
            return pd.DataFrame()

        try:
            df = pd.read_excel(filepath, engine='openpyxl')
        except Exception:
            try:
                df = pd.read_excel(filepath)  # fallback
            except Exception:
                return pd.DataFrame()

        if df.empty:
            return pd.DataFrame()

        return self._normalize_dataframe(df)

    def _normalize_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        """Normaliza colunas essenciais e aplica regras de negócio."""
        finder = ColumnFinder(df)

        # Mapear colunas essenciais
        doc_col = finder.find_column(['documento', 'nr documento', 'nº documento', 'num doc'])
        valor_col = finder.find_column(['valor', 'valor pago', 'valor recebido', 'vlr pago', 'vlr recebido'])
        data_col = finder.find_column(['data', 'data pagamento', 'dt pagamento', 'data recebimento'])
        cliente_col = finder.find_column(['id_cliente', 'id cliente', 'código cliente', 'codigo cliente', 'cliente'])

        if doc_col is None or valor_col is None:
            # Sem documento ou valor, não é possível processar
            return pd.DataFrame()

        # Criar colunas destino
        out = pd.DataFrame()
        out['DOCUMENTO_ORIGINAL'] = df[doc_col].astype(str).str.strip()
        out['VALOR_PAGO'] = pd.to_numeric(df[valor_col], errors='coerce').fillna(0.0)

        if data_col:
            out['DATA_PAGAMENTO'] = pd.to_datetime(df[data_col], errors='coerce')
        else:
            out['DATA_PAGAMENTO'] = pd.NaT

        if cliente_col:
            out['ID_CLIENTE'] = df[cliente_col]
        else:
            out['ID_CLIENTE'] = None

        # Regras de classificação
        doc_upper = out['DOCUMENTO_ORIGINAL'].str.upper().fillna('')
        is_adiant = doc_upper.str.startswith('COT')

        out['TIPO_PAGAMENTO'] = is_adiant.map({True: 'Antecipação', False: 'Pagamento Regular'})

        # Extrair PROCESSO para antecipações (apenas dígitos após 'COT')
        out['PROCESSO'] = None
        mask_a = is_adiant
        if mask_a.any():
            sufixos = out.loc[mask_a, 'DOCUMENTO_ORIGINAL'].str.upper().str.replace('COT', '', regex=False)
            out.loc[mask_a, 'PROCESSO'] = sufixos.str.extract(r'(\d+)')[0].str.strip()

        # Normalizar documento NF (6 primeiros dígitos) para pagamentos regulares
        out['DOCUMENTO_NORMALIZADO'] = None
        mask_r = ~is_adiant
        if mask_r.any():
            # Manter apenas dígitos e pegar os 6 primeiros
            only_digits = out.loc[mask_r, 'DOCUMENTO_ORIGINAL'].str.replace(r'\D', '', regex=True)
            out.loc[mask_r, 'DOCUMENTO_NORMALIZADO'] = only_digits.str.slice(0, 6)

        # Filtrar entradas inválidas (sem valor ou sem identificadores básicos)
        out = out[pd.to_numeric(out['VALOR_PAGO'], errors='coerce').fillna(0.0) != 0.0].copy()

        return out.reset_index(drop=True)


