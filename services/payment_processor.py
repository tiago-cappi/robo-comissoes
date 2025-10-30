"""
Processamento completo de recebimentos.

Este módulo orquestra o fluxo completo de processamento de recebimentos:
1. Mapear recebimento para processo
2. Extrair contexto do processo
3. Calcular comissões
4. Atualizar estado
"""

import pandas as pd
import sys
import os
from typing import Tuple, List, Dict

# Adicionar path para imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from .payment_mapper import PaymentMapper
from .payment_commission_calculator import PaymentCommissionCalculator


class PaymentProcessor:
    """
    Orquestra o processamento completo de recebimentos.
    
    Este é o ponto de entrada principal para processar recebimentos,
    coordenando mapper, calculator e atualização de estado.
    
    Attributes:
        recebimentos_df: DataFrame com recebimentos do mês
        mapper: PaymentMapper para mapear recebimentos
        calculator: PaymentCommissionCalculator para calcular comissões
        state_manager: ProcessStateManager para atualizar estado (opcional)
    """
    
    def __init__(self,
                 recebimentos_df: pd.DataFrame,
                 analise_comercial_df: pd.DataFrame,
                 commission_calculator: PaymentCommissionCalculator,
                 state_manager=None):
        """
        Inicializa o processador.
        
        Args:
            recebimentos_df: DataFrame com recebimentos (PROCESSO, VALOR_RECEBIDO, DATA_RECEBIMENTO, ID_CLIENTE)
            analise_comercial_df: DataFrame com análise comercial completa
            commission_calculator: Calculador de comissões
            state_manager: ProcessStateManager para atualizar estado (opcional)
        """
        self.recebimentos_df = recebimentos_df
        self.mapper = PaymentMapper(analise_comercial_df)
        self.calculator = commission_calculator
        self.state_manager = state_manager
    
    def process_all_payments(self) -> Tuple[pd.DataFrame, List[Dict]]:
        """
        Processa todos os recebimentos.
        
        Fluxo:
        1. Para cada recebimento, mapear para processo
        2. Extrair contexto do processo
        3. Calcular comissões
        4. Atualizar estado (se state_manager fornecido)
        5. Retornar DataFrame de comissões e log de mapeamentos
        
        Returns:
            Tupla (comissoes_df, log_mapeamentos):
                - comissoes_df: DataFrame com comissões calculadas
                - log_mapeamentos: Lista de dicts com informações de mapeamento
        """
        if self.recebimentos_df.empty:
            return pd.DataFrame(), []
        
        comissoes_list = []
        log_mapeamentos = []
        
        for _, payment_row in self.recebimentos_df.iterrows():
            processo = payment_row.get('PROCESSO')
            valor_recebido = payment_row.get('VALOR_RECEBIDO')
            id_cliente = payment_row.get('ID_CLIENTE')
            data_recebimento = payment_row.get('DATA_RECEBIMENTO')
            
            # Validar dados básicos
            if pd.isna(processo) or pd.isna(valor_recebido):
                log_mapeamentos.append({
                    'processo': processo,
                    'valor_recebido': valor_recebido,
                    'status': 'DADOS_INVALIDOS',
                    'metodo': None,
                    'comissoes_geradas': 0
                })
                continue
            
            # 1. Mapear recebimento para processo na análise comercial
            mapped_row, map_method = self.mapper.map_payment(
                processo, valor_recebido, id_cliente
            )
            
            if mapped_row is None:
                # Não conseguiu mapear - criar registro placeholder
                comissoes_list.append({
                    'id_colaborador': None,
                    'nome_colaborador': None,
                    'cargo': None,
                    'processo': processo,
                    'linha': None,
                    'grupo': None,
                    'subgrupo': None,
                    'tipo_mercadoria': None,
                    'faturamento_item': valor_recebido,
                    'taxa_rateio_aplicada': None,
                    'percentual_elegibilidade_pe': None,
                    'fator_correcao_fc': None,
                    'comissao_calculada': None,
                    'tipo_lancamento': 'Recebimento',
                    'observacao': 'Processo nao mapeado',
                    'mapping_found': False
                })
                
                log_mapeamentos.append({
                    'processo': processo,
                    'valor_recebido': valor_recebido,
                    'status': 'NAO_MAPEADO',
                    'metodo': map_method,
                    'comissoes_geradas': 0
                })
                continue
            
            # 2. Extrair contexto do processo
            process_context = self.mapper.get_process_context(mapped_row)
            
            # 3. Calcular comissões para colaboradores que recebem por recebimento
            comissoes = self.calculator.calculate_for_payment(
                processo, valor_recebido, process_context
            )
            
            # Adicionar dados adicionais às comissões (data de recebimento, etc)
            for comissao in comissoes:
                if pd.notna(data_recebimento):
                    comissao['data_recebimento'] = data_recebimento
                comissao['mapping_found'] = True
                comissao['mapping_method'] = map_method
            
            comissoes_list.extend(comissoes)
            
            # 4. Atualizar estado (se fornecido)
            if self.state_manager is not None:
                self._update_state_for_payment(
                    processo, 
                    valor_recebido, 
                    comissoes, 
                    process_context
                )
            
            # Log de mapeamento
            log_mapeamentos.append({
                'processo': processo,
                'valor_recebido': valor_recebido,
                'status': 'MAPEADO',
                'metodo': map_method,
                'linha': process_context.get('linha'),
                'comissoes_geradas': len(comissoes)
            })
        
        # Converter lista para DataFrame
        comissoes_df = pd.DataFrame(comissoes_list) if comissoes_list else pd.DataFrame()
        
        return comissoes_df, log_mapeamentos
    
    def _update_state_for_payment(self, processo: str, valor_recebido: float,
                                  comissoes: List[Dict], process_context: Dict) -> None:
        """
        Atualiza estado para um recebimento processado.
        
        Args:
            processo: ID do processo
            valor_recebido: Valor recebido
            comissoes: Lista de comissões calculadas
            process_context: Contexto do processo
        """
        if self.state_manager is None:
            return
        
        # Atualizar valor pago acumulado
        valor_total_processo = process_context.get('valor_processo')
        self.state_manager.update_payment_received(
            processo,
            valor_recebido,
            valor_total_processo=valor_total_processo
        )
        
        # Atualizar comissão adiantada acumulada
        total_comissao = sum(c.get('comissao_calculada', 0.0) for c in comissoes)
        if total_comissao > 0:
            self.state_manager.update_commission_advanced(processo, total_comissao)
    
    def get_processing_summary(self, log_mapeamentos: List[Dict]) -> Dict:
        """
        Retorna resumo do processamento.
        
        Args:
            log_mapeamentos: Lista de logs retornada por process_all_payments
        
        Returns:
            Dicionário com estatísticas
        """
        if not log_mapeamentos:
            return {
                'total_recebimentos': 0,
                'mapeados': 0,
                'nao_mapeados': 0,
                'dados_invalidos': 0,
                'taxa_mapeamento': 0.0,
                'total_comissoes_geradas': 0
            }
        
        total = len(log_mapeamentos)
        mapeados = sum(1 for log in log_mapeamentos if log['status'] == 'MAPEADO')
        nao_mapeados = sum(1 for log in log_mapeamentos if log['status'] == 'NAO_MAPEADO')
        invalidos = sum(1 for log in log_mapeamentos if log['status'] == 'DADOS_INVALIDOS')
        total_comissoes = sum(log.get('comissoes_geradas', 0) for log in log_mapeamentos)
        
        return {
            'total_recebimentos': total,
            'mapeados': mapeados,
            'nao_mapeados': nao_mapeados,
            'dados_invalidos': invalidos,
            'taxa_mapeamento': (mapeados / total * 100) if total > 0 else 0.0,
            'total_comissoes_geradas': total_comissoes
        }
    
    def get_unmapped_payments(self, log_mapeamentos: List[Dict]) -> List[Dict]:
        """
        Retorna recebimentos que não foram mapeados.
        
        Útil para debugging e análise de problemas de mapeamento.
        
        Args:
            log_mapeamentos: Lista de logs retornada por process_all_payments
        
        Returns:
            Lista de recebimentos não mapeados
        """
        return [
            log for log in log_mapeamentos 
            if log['status'] in ('NAO_MAPEADO', 'DADOS_INVALIDOS')
        ]

