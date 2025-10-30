"""
Construção de métricas realizadas (séries de faturamento, conversão, rentabilidade).

Este módulo constrói séries pandas agregadas a partir de DataFrames históricos
para uso no cálculo do Fator de Correção (FC).
"""

import pandas as pd
import sys
import os
from typing import Dict, Optional

# Adicionar path para imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.column_finder import ColumnFinder


class RealizedMetricsBuilder:
    """
    Constrói séries de métricas realizadas para cálculo de FC.
    
    Séries construídas:
    - faturamento_linha: soma de Valor Realizado por Linha (Negócio)
    - faturamento_individual: soma de Valor Realizado por Consultor
    - conversao_linha: soma de Valor Orçado por Linha
    - conversao_individual: soma de Valor Orçado por Consultor
    - rentabilidade: rentabilidade por (linha, grupo, subgrupo, tipo_mercadoria)
    """
    
    def build_from_dataframes(self,
                             faturados_df: pd.DataFrame,
                             conversoes_df: pd.DataFrame,
                             rentabilidade_df: pd.DataFrame) -> Dict[str, pd.Series]:
        """
        Constrói séries de realizados a partir dos DataFrames.
        
        Args:
            faturados_df: DataFrame de faturados
            conversoes_df: DataFrame de conversões
            rentabilidade_df: DataFrame de rentabilidade
        
        Returns:
            Dicionário com séries:
            {
                'faturamento_linha': pd.Series,
                'faturamento_individual': pd.Series,
                'conversao_linha': pd.Series,
                'conversao_individual': pd.Series,
                'rentabilidade': pd.Series (multi-índice)
            }
        """
        # Construir cada série
        series = {
            'faturamento_linha': self._build_faturamento_linha(faturados_df),
            'faturamento_individual': self._build_faturamento_individual(faturados_df),
            'conversao_linha': self._build_conversao_linha(conversoes_df),
            'conversao_individual': self._build_conversao_individual(conversoes_df),
            'rentabilidade': self._build_rentabilidade(rentabilidade_df)
        }
        
        # Garantir que todas sejam Series (mesmo que vazias)
        for key in series:
            if not isinstance(series[key], pd.Series):
                series[key] = pd.Series(dtype=float)
        
        return series
    
    def _build_faturamento_linha(self, df: pd.DataFrame) -> pd.Series:
        """
        Constrói série de faturamento por linha.
        
        Agrega: Valor Realizado por Negócio (Linha)
        """
        if df.empty:
            return pd.Series(dtype=float)
        
        finder = ColumnFinder(df)
        linha_col = finder.find_column(['negocio', 'negócio', 'linha'])
        valor_col = finder.find_column(['valor realizado', 'valor_realizado', 'valor nf', 'faturamento'])
        
        return self._build_group_series(df, linha_col, valor_col)
    
    def _build_faturamento_individual(self, df: pd.DataFrame) -> pd.Series:
        """
        Constrói série de faturamento individual.
        
        Agrega: Valor Realizado por Consultor Interno
        """
        if df.empty:
            return pd.Series(dtype=float)
        
        finder = ColumnFinder(df)
        consultor_col = finder.find_column(['consultor interno', 'consultorinterno', 'consultor'])
        valor_col = finder.find_column(['valor realizado', 'valor_realizado', 'valor nf', 'faturamento'])
        
        return self._build_group_series(df, consultor_col, valor_col)
    
    def _build_conversao_linha(self, df: pd.DataFrame) -> pd.Series:
        """
        Constrói série de conversão por linha.
        
        Agrega: Valor Orçado por Negócio (Linha)
        """
        if df.empty:
            return pd.Series(dtype=float)
        
        finder = ColumnFinder(df)
        linha_col = finder.find_column(['negocio', 'negócio', 'linha'])
        valor_col = finder.find_column(['valor orçado', 'valor orcado', 'valor_orcado'])
        
        return self._build_group_series(df, linha_col, valor_col)
    
    def _build_conversao_individual(self, df: pd.DataFrame) -> pd.Series:
        """
        Constrói série de conversão individual.
        
        Agrega: Valor Orçado por Consultor Interno
        """
        if df.empty:
            return pd.Series(dtype=float)
        
        finder = ColumnFinder(df)
        consultor_col = finder.find_column(['consultor interno', 'consultorinterno', 'consultor'])
        valor_col = finder.find_column(['valor orçado', 'valor orcado', 'valor_orcado'])
        
        return self._build_group_series(df, consultor_col, valor_col)
    
    def _build_rentabilidade(self, df: pd.DataFrame) -> pd.Series:
        """
        Constrói série multi-índice de rentabilidade.
        
        Índice: (linha, grupo, subgrupo, tipo_mercadoria)
        Valor: rentabilidade_realizada_pct
        """
        if df.empty:
            return pd.Series(dtype=float)
        
        finder = ColumnFinder(df)
        
        linha_col = finder.find_column(['negocio', 'negócio', 'linha'])
        grupo_col = finder.find_column(['grupo'])
        subgrupo_col = finder.find_column(['subgrupo'])
        tipo_col = finder.find_column(['tipo de mercadoria', 'tipo mercadoria', 'tipomercadoria'])
        valor_col = finder.find_column(['rentabilidade_realizada_pct', 'rentabilidade realizada', 'rentabilidade'])
        
        # Verificar se temos todas as colunas necessárias
        if None in (linha_col, grupo_col, subgrupo_col, tipo_col, valor_col):
            return pd.Series(dtype=float)
        
        # Preparar DataFrame
        df_copy = df[[linha_col, grupo_col, subgrupo_col, tipo_col, valor_col]].copy()
        
        # Converter para string (índice)
        for col in (linha_col, grupo_col, subgrupo_col, tipo_col):
            df_copy[col] = df_copy[col].astype(str).str.strip()
        
        # Converter valor para numérico
        df_copy[valor_col] = pd.to_numeric(df_copy[valor_col], errors='coerce').fillna(0.0)
        
        # Criar série multi-índice
        return df_copy.set_index([linha_col, grupo_col, subgrupo_col, tipo_col])[valor_col]
    
    def _build_group_series(self, df: pd.DataFrame, 
                           group_col: Optional[str], 
                           value_col: Optional[str]) -> pd.Series:
        """
        Constrói série agregada (soma por grupo).
        
        Args:
            df: DataFrame fonte
            group_col: Coluna para agrupar
            value_col: Coluna para somar
        
        Returns:
            pd.Series com soma por grupo, ou série vazia se colunas não existirem
        """
        if df.empty or group_col is None or value_col is None:
            return pd.Series(dtype=float)
        
        try:
            # Preparar dados
            data = df[[group_col, value_col]].copy()
            data[group_col] = data[group_col].astype(str).str.strip()
            data[value_col] = pd.to_numeric(data[value_col], errors='coerce').fillna(0.0)
            
            # Agrupar e somar
            return data.groupby(group_col)[value_col].sum()
            
        except Exception:
            return pd.Series(dtype=float)
    
    def validate_series(self, series_dict: Dict[str, pd.Series]) -> Dict[str, Dict]:
        """
        Valida séries construídas e retorna estatísticas.
        
        Útil para debugging e validação de dados históricos.
        
        Args:
            series_dict: Dicionário retornado por build_from_dataframes
        
        Returns:
            Dicionário com estatísticas por série:
            {
                'faturamento_linha': {'count': int, 'total': float, 'valid': bool},
                ...
            }
        """
        stats = {}
        
        for key, series in series_dict.items():
            if isinstance(series, pd.Series):
                stats[key] = {
                    'count': len(series),
                    'total': float(series.sum()) if not series.empty else 0.0,
                    'valid': not series.empty,
                    'type': 'Series',
                    'index_type': str(type(series.index)) if not series.empty else None
                }
            else:
                stats[key] = {
                    'count': 0,
                    'total': 0.0,
                    'valid': False,
                    'type': str(type(series)),
                    'index_type': None
                }
        
        return stats

