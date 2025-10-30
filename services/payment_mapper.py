"""
Mapeamento de recebimentos para processos da análise comercial.

Este módulo implementa as estratégias de mapeamento de recebimentos para processos,
usando múltiplas abordagens progressivas (exact match, substring, cliente+valor, etc).
"""

import pandas as pd
import sys
import os
from typing import Tuple, Optional, Dict

# Adicionar path para importar utils
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.normalization import normalize_process_id
from utils.column_finder import ColumnFinder


class PaymentMapper:
    """
    Mapeia recebimentos para processos usando estratégias progressivas.
    
    O mapeamento tenta várias estratégias em ordem de confiabilidade:
    1. Match exato de processo (normalizado)
    2. Match por substring
    3. Match por cliente + valor aproximado (não implementado ainda)
    4. Match por truncamento numérico (não implementado ainda)
    
    Attributes:
        analise_df: DataFrame com análise comercial completa
        column_finder: ColumnFinder para buscar colunas
        processo_col: Nome da coluna de processo
        valor_col: Nome da coluna de valor
        cliente_col: Nome da coluna de cliente
    """
    
    def __init__(self, analise_comercial_df: pd.DataFrame):
        """
        Inicializa o mapper com o DataFrame de análise comercial.
        
        Args:
            analise_comercial_df: DataFrame com análise comercial completa
        """
        self.analise_df = analise_comercial_df
        self.column_finder = ColumnFinder(analise_comercial_df)
        
        # Buscar colunas importantes
        self.processo_col = self.column_finder.find_column(['processo', 'id processo', 'id_processo'])
        self.valor_col = self.column_finder.find_column(['valor realizado', 'valor_realizado', 'valorrealizado'])
        self.cliente_col = self.column_finder.find_column(['cliente', 'id cliente', 'id_cliente'])
        
        # Cache de processos normalizados para performance
        if self.processo_col:
            self._processo_normalized = self.analise_df[self.processo_col].apply(normalize_process_id)
        else:
            self._processo_normalized = pd.Series(dtype=str)
    
    def map_payment(self, processo_val, valor_val: float = None, 
                   id_cliente_val = None) -> Tuple[Optional[pd.Series], str]:
        """
        Mapeia um recebimento para um processo.
        
        Tenta múltiplas estratégias em ordem decrescente de confiabilidade.
        
        Args:
            processo_val: ID do processo do recebimento
            valor_val: Valor recebido (opcional, usado para desempate)
            id_cliente_val: ID do cliente (opcional, usado para cliente+valor match)
        
        Returns:
            Tupla (linha_mapeada, método_usado):
                - linha_mapeada: pd.Series com a linha encontrada, ou None
                - método_usado: string indicando o método ('exact_match', 'substring_match', etc)
        
        Examples:
            >>> mapper = PaymentMapper(analise_df)
            >>> row, method = mapper.map_payment(999999, 1000.0)
            >>> if row is not None:
            ...     print(f"Processo mapeado via {method}")
        """
        if self.processo_col is None:
            return None, 'no_processo_column'
        
        # Normalizar processo de entrada
        proc_normalized = normalize_process_id(processo_val)
        if proc_normalized is None:
            return None, 'invalid_processo'
        
        # Estratégia 1: Match exato (normalizado)
        mapped_row = self._try_exact_match(proc_normalized)
        if mapped_row is not None:
            return mapped_row, 'exact_match'
        
        # Estratégia 2: Match por substring
        mapped_row = self._try_substring_match(proc_normalized, valor_val)
        if mapped_row is not None:
            method = 'substring_match_with_value' if valor_val is not None else 'substring_match'
            return mapped_row, method
        
        # Nenhuma estratégia funcionou
        return None, 'not_found'
    
    def _try_exact_match(self, proc_normalized: str) -> Optional[pd.Series]:
        """
        Tenta match exato de processo (normalizado).
        
        Args:
            proc_normalized: Processo normalizado
        
        Returns:
            Primeira linha que deu match, ou None
        """
        if self._processo_normalized.empty:
            return None
        
        exact_mask = self._processo_normalized == proc_normalized
        if exact_mask.any():
            return self.analise_df[exact_mask].iloc[0]
        
        return None
    
    def _try_substring_match(self, proc_normalized: str, 
                            valor_val: Optional[float] = None) -> Optional[pd.Series]:
        """
        Tenta match por substring (processo contido ou contém).
        
        Se houver múltiplos candidatos e valor_val for fornecido, escolhe
        o candidato com valor mais próximo.
        
        Args:
            proc_normalized: Processo normalizado
            valor_val: Valor para desempate (opcional)
        
        Returns:
            Melhor linha candidata, ou None
        """
        if self._processo_normalized.empty:
            return None
        
        # Buscar por substring (bidirecional)
        substring_mask = self._processo_normalized.apply(
            lambda x: (str(x) in proc_normalized) or (proc_normalized in str(x)) 
            if pd.notna(x) else False
        )
        
        candidates = self.analise_df[substring_mask]
        
        if candidates.empty:
            return None
        
        # Se há apenas um candidato, retornar
        if len(candidates) == 1:
            return candidates.iloc[0]
        
        # Se há múltiplos e temos valor, escolher o mais próximo
        if valor_val is not None and self.valor_col is not None:
            return self._choose_closest_by_value(candidates, valor_val)
        
        # Fallback: retornar primeiro candidato
        return candidates.iloc[0]
    
    def _choose_closest_by_value(self, candidates: pd.DataFrame, 
                                 target_value: float) -> pd.Series:
        """
        Escolhe candidato com valor mais próximo do target.
        
        Args:
            candidates: DataFrame com candidatos
            target_value: Valor alvo
        
        Returns:
            Linha do candidato com valor mais próximo
        """
        try:
            candidates = candidates.copy()
            candidates['_diff'] = candidates[self.valor_col].apply(
                lambda x: abs((float(x) if pd.notna(x) else 0.0) - target_value)
            )
            candidates_sorted = candidates.sort_values('_diff')
            return candidates_sorted.iloc[0]
        except Exception:
            # Em caso de erro, retornar primeiro candidato
            return candidates.iloc[0]
    
    def get_process_context(self, mapped_row: pd.Series) -> Dict:
        """
        Extrai contexto do processo (linha, grupo, subgrupo, tipo, etc).
        
        Args:
            mapped_row: Linha mapeada do DataFrame de análise
        
        Returns:
            Dicionário com contexto do processo
        """
        finder = ColumnFinder(pd.DataFrame([mapped_row]))
        
        return {
            'processo': normalize_process_id(mapped_row.get(self.processo_col)) if self.processo_col else None,
            'linha': self._get_value(mapped_row, ['negocio', 'negócio', 'linha']),
            'grupo': self._get_value(mapped_row, ['grupo']),
            'subgrupo': self._get_value(mapped_row, ['subgrupo']),
            'tipo_mercadoria': self._get_value(mapped_row, ['tipo de mercadoria', 'tipo mercadoria', 'tipomercadoria']),
            'cliente': self._get_value(mapped_row, ['cliente', 'nome cliente', 'nomecliente']),
            'valor_processo': self._get_value_numeric(mapped_row, ['valor realizado', 'valor_realizado', 'valorrealizado']),
            'consultor_interno': self._get_value(mapped_row, ['consultor interno', 'consultorinterno', 'consultor']),
            'representante': self._get_value(mapped_row, ['representante-pedido', 'representante pedido', 'representante'])
        }
    
    def _get_value(self, row: pd.Series, column_aliases: list) -> Optional[str]:
        """
        Busca valor em uma linha por lista de aliases de coluna.
        
        Args:
            row: Série do pandas
            column_aliases: Lista de possíveis nomes da coluna
        
        Returns:
            Valor encontrado ou None
        """
        # Criar DataFrame temporário para usar ColumnFinder
        temp_df = pd.DataFrame([row])
        finder = ColumnFinder(temp_df)
        col = finder.find_column(column_aliases)
        
        if col is not None:
            value = row.get(col)
            return str(value).strip() if pd.notna(value) else None
        
        return None
    
    def _get_value_numeric(self, row: pd.Series, column_aliases: list) -> Optional[float]:
        """
        Busca valor numérico em uma linha.
        
        Args:
            row: Série do pandas
            column_aliases: Lista de possíveis nomes da coluna
        
        Returns:
            Valor numérico ou None
        """
        value = self._get_value(row, column_aliases)
        if value is None:
            return None
        
        try:
            return float(value)
        except (ValueError, TypeError):
            return None
    
    def get_mapping_statistics(self, recebimentos_df: pd.DataFrame) -> Dict:
        """
        Retorna estatísticas de mapeamento para um conjunto de recebimentos.
        
        Args:
            recebimentos_df: DataFrame com recebimentos
        
        Returns:
            Dicionário com estatísticas
        """
        if recebimentos_df.empty:
            return {
                'total': 0,
                'mapped': 0,
                'not_mapped': 0,
                'mapping_rate': 0.0,
                'by_method': {}
            }
        
        total = len(recebimentos_df)
        methods = {}
        mapped = 0
        
        for _, rec in recebimentos_df.iterrows():
            processo = rec.get('PROCESSO')
            valor = rec.get('VALOR_RECEBIDO')
            cliente = rec.get('ID_CLIENTE')
            
            _, method = self.map_payment(processo, valor, cliente)
            
            if method != 'not_found':
                mapped += 1
            
            methods[method] = methods.get(method, 0) + 1
        
        return {
            'total': total,
            'mapped': mapped,
            'not_mapped': total - mapped,
            'mapping_rate': (mapped / total * 100) if total > 0 else 0.0,
            'by_method': methods
        }

