"""
Utilitários para localizar colunas em DataFrames.

Este módulo fornece uma interface consistente para buscar colunas em DataFrames
com diferentes variações de nomes, eliminando código duplicado e tornando
as buscas mais robustas.
"""

import pandas as pd
from typing import List, Optional, Dict
from .normalization import normalize_column_name


class ColumnFinder:
    """
    Classe auxiliar para encontrar colunas em DataFrames com nomes variados.
    
    Esta classe permite buscar colunas tolerando diferenças de:
    - Case (maiúsculas/minúsculas)
    - Acentuação
    - BOM (Byte Order Mark)
    - Espaços extras
    
    Attributes:
        df: DataFrame onde as colunas serão buscadas
        _column_map: Mapeamento cache de nomes normalizados -> nomes originais
    
    Examples:
        >>> df = pd.DataFrame(columns=['Valor Realizado', 'Consultor Interno'])
        >>> finder = ColumnFinder(df)
        >>> finder.find_column(['valor realizado', 'valor_realizado'])
        'Valor Realizado'
        >>> finder.find_column(['nao existe'])
        None
    """
    
    def __init__(self, df: pd.DataFrame):
        """
        Inicializa o ColumnFinder com um DataFrame.
        
        Args:
            df: DataFrame cujas colunas serão buscadas
        """
        self.df = df
        # Criar cache de mapeamento normalizado -> original
        self._column_map = {
            normalize_column_name(col): col 
            for col in df.columns
        }
    
    def find_column(self, aliases: List[str]) -> Optional[str]:
        """
        Busca uma coluna por lista de aliases (nomes alternativos).
        
        Retorna o primeiro alias que encontrar uma correspondência.
        A busca é case-insensitive e ignora acentos/espaços.
        
        Args:
            aliases: Lista de possíveis nomes para a coluna
        
        Returns:
            Nome original da coluna encontrada, ou None se não encontrar
        
        Examples:
            >>> finder.find_column(['valor realizado', 'valor_realizado', 'faturamento'])
            'Valor Realizado'  # se existir no DataFrame
        """
        if not aliases:
            return None
        
        for alias in aliases:
            normalized_alias = normalize_column_name(alias)
            if normalized_alias in self._column_map:
                return self._column_map[normalized_alias]
        
        return None
    
    def find_all_columns(self, alias_groups: Dict[str, List[str]]) -> Dict[str, Optional[str]]:
        """
        Busca múltiplas colunas de uma vez.
        
        Esta é uma versão otimizada para buscar várias colunas simultaneamente,
        útil quando você precisa encontrar múltiplas colunas no mesmo DataFrame.
        
        Args:
            alias_groups: Dicionário onde:
                - chave: identificador da coluna (ex: 'processo', 'valor')
                - valor: lista de aliases para buscar
        
        Returns:
            Dicionário com identificador -> nome original da coluna (ou None)
        
        Examples:
            >>> alias_groups = {
            ...     'processo': ['processo', 'id processo'],
            ...     'valor': ['valor realizado', 'faturamento'],
            ...     'consultor': ['consultor interno', 'consultor']
            ... }
            >>> finder.find_all_columns(alias_groups)
            {'processo': 'Processo', 'valor': 'Valor Realizado', 'consultor': 'Consultor Interno'}
        """
        results = {}
        for key, aliases in alias_groups.items():
            results[key] = self.find_column(aliases)
        return results
    
    def has_column(self, aliases: List[str]) -> bool:
        """
        Verifica se algum dos aliases existe no DataFrame.
        
        Args:
            aliases: Lista de possíveis nomes para a coluna
        
        Returns:
            True se encontrar a coluna, False caso contrário
        
        Examples:
            >>> finder.has_column(['valor realizado'])
            True
            >>> finder.has_column(['coluna inexistente'])
            False
        """
        return self.find_column(aliases) is not None
    
    def get_column_or_default(self, aliases: List[str], default_value=None) -> str:
        """
        Busca coluna ou retorna valor padrão se não encontrar.
        
        Útil quando você quer garantir que sempre terá um valor (mesmo que None).
        
        Args:
            aliases: Lista de possíveis nomes para a coluna
            default_value: Valor a retornar se não encontrar (default: None)
        
        Returns:
            Nome da coluna ou default_value
        """
        result = self.find_column(aliases)
        return result if result is not None else default_value


def find_column_simple(df: pd.DataFrame, aliases: List[str]) -> Optional[str]:
    """
    Função auxiliar para busca simples de coluna sem criar instância de ColumnFinder.
    
    Útil para buscas pontuais onde não vale a pena criar uma instância da classe.
    
    Args:
        df: DataFrame onde buscar
        aliases: Lista de possíveis nomes para a coluna
    
    Returns:
        Nome original da coluna ou None
    
    Examples:
        >>> find_column_simple(df, ['processo', 'id processo'])
        'Processo'
    """
    finder = ColumnFinder(df)
    return finder.find_column(aliases)

