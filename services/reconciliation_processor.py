"""
Processamento completo de reconciliações retroativas.

Este módulo orquestra o processamento de todas as reconciliações elegíveis,
coordenando calculador, state manager e geração de resumos.
"""

import pandas as pd
import sys
import os
from typing import Tuple, List, Dict

# Adicionar path para imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from .reconciliation_calculator import ReconciliationCalculator


class ReconciliationProcessor:
    """
    Orquestra o processamento de reconciliações retroativas.
    
    Este serviço:
    1. Busca processos elegíveis (Quitado + Faturado + Não Reconciliado)
    2. Para cada um, calcula reconciliação com ReconciliationCalculator
    3. Gera tabelas detalhadas e resumo
    4. Atualiza estado (marca como reconciliado)
    
    Attributes:
        state_manager: ProcessStateManager para gerenciar estado
        calculator: ReconciliationCalculator para calcular reconciliações
    """
    
    def __init__(self,
                 state_manager,
                 reconciliation_calculator: ReconciliationCalculator):
        """
        Inicializa o processador.
        
        Args:
            state_manager: ProcessStateManager (models.process_state.ProcessStateManager)
            reconciliation_calculator: ReconciliationCalculator para cálculos
        """
        self.state_manager = state_manager
        self.calculator = reconciliation_calculator
    
    def process_all_eligible(self) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """
        Processa todas as reconciliações elegíveis.
        
        Fluxo:
        1. Obter processos elegíveis do estado
        2. Para cada processo:
           a. Calcular reconciliação (item a item)
           b. Calcular saldo (comissão correta - adiantamentos)
           c. Marcar como reconciliado
        3. Gerar DataFrames: detalhado (item a item) e resumo (por processo)
        
        Returns:
            Tupla (detalhada_df, resumo_df):
                - detalhada_df: Linhas item a item com comissões recalculadas
                - resumo_df: Resumo por processo (total correto, adiantado, saldo)
        """
        # 1. Obter processos elegíveis
        eligible_processes = self.state_manager.get_eligible_for_reconciliation()
        
        if eligible_processes.empty:
            print("[Reconc-Info] Nenhum processo elegível para reconciliação")
            return pd.DataFrame(), pd.DataFrame()
        
        print(f"[Reconc-Info] {len(eligible_processes)} processo(s) elegível(is) para reconciliação")
        
        detalhadas_list = []
        resumo_list = []
        
        # 2. Processar cada processo
        for _, process_row in eligible_processes.iterrows():
            processo_id = process_row['PROCESSO']
            total_adiantado = float(process_row.get('TOTAL_ADIANTADO_COMISSAO', 0.0))
            
            try:
                print(f"[Reconc-Info] Processando {processo_id}...")
                
                # 2a. Calcular reconciliação
                linhas_detalhadas, comissao_correta = self.calculator.reconcile_process(
                    processo_id
                )
                
                if not linhas_detalhadas:
                    print(f"[Reconc-Aviso] Reconciliação para {processo_id} não gerou linhas")
                    continue
                
                # 2b. Calcular saldo
                saldo_final = comissao_correta - total_adiantado
                
                # 2c. Acumular resultados
                detalhadas_list.extend(linhas_detalhadas)
                resumo_list.append({
                    'PROCESSO': processo_id,
                    'COMISSAO_CORRETA_TOTAL': comissao_correta,
                    'TOTAL_ADIANTAMENTOS_PAGOS': total_adiantado,
                    'SALDO_FINAL_RECONCILIACAO': saldo_final
                })
                
                # 2d. Marcar como reconciliado
                self.state_manager.mark_reconciliation_done(processo_id)
                
                print(f"[Reconc-Sucesso] {processo_id}: Comissão={comissao_correta:.2f}, Adiantado={total_adiantado:.2f}, Saldo={saldo_final:.2f}")
                
            except Exception as e:
                print(f"[Reconc-Erro] Falha ao processar {processo_id}: {e}")
                # Não marcar como erro no estado para permitir retry
                continue
        
        # 3. Converter para DataFrames
        detalhada_df = pd.DataFrame(detalhadas_list) if detalhadas_list else pd.DataFrame()
        resumo_df = pd.DataFrame(resumo_list) if resumo_list else pd.DataFrame()
        
        return detalhada_df, resumo_df
    
    def get_processing_summary(self, resumo_df: pd.DataFrame) -> Dict:
        """
        Retorna resumo estatístico do processamento.
        
        Args:
            resumo_df: DataFrame de resumo retornado por process_all_eligible
        
        Returns:
            Dicionário com estatísticas
        """
        if resumo_df.empty:
            return {
                'total_processos': 0,
                'comissao_correta_total': 0.0,
                'adiantamentos_pagos_total': 0.0,
                'saldo_final_total': 0.0,
                'processos_com_saldo_positivo': 0,
                'processos_com_saldo_negativo': 0,
                'processos_com_saldo_zero': 0
            }
        
        saldo_positivo = (resumo_df['SALDO_FINAL_RECONCILIACAO'] > 0).sum()
        saldo_negativo = (resumo_df['SALDO_FINAL_RECONCILIACAO'] < 0).sum()
        saldo_zero = (resumo_df['SALDO_FINAL_RECONCILIACAO'] == 0).sum()
        
        return {
            'total_processos': len(resumo_df),
            'comissao_correta_total': float(resumo_df['COMISSAO_CORRETA_TOTAL'].sum()),
            'adiantamentos_pagos_total': float(resumo_df['TOTAL_ADIANTAMENTOS_PAGOS'].sum()),
            'saldo_final_total': float(resumo_df['SALDO_FINAL_RECONCILIACAO'].sum()),
            'processos_com_saldo_positivo': int(saldo_positivo),
            'processos_com_saldo_negativo': int(saldo_negativo),
            'processos_com_saldo_zero': int(saldo_zero)
        }
    
    def get_processes_requiring_payment(self, resumo_df: pd.DataFrame, 
                                       threshold: float = 0.01) -> pd.DataFrame:
        """
        Retorna processos que requerem pagamento adicional.
        
        Filtra processos com saldo positivo acima do threshold (diferença a pagar).
        
        Args:
            resumo_df: DataFrame de resumo
            threshold: Valor mínimo para considerar (default: R$ 0,01)
        
        Returns:
            DataFrame filtrado com processos a pagar
        """
        if resumo_df.empty:
            return pd.DataFrame()
        
        return resumo_df[resumo_df['SALDO_FINAL_RECONCILIACAO'] > threshold].copy()
    
    def get_processes_with_overpayment(self, resumo_df: pd.DataFrame,
                                      threshold: float = 0.01) -> pd.DataFrame:
        """
        Retorna processos com pagamento a maior (adiantamento excessivo).
        
        Filtra processos com saldo negativo abaixo do threshold (pago a mais).
        
        Args:
            resumo_df: DataFrame de resumo
            threshold: Valor mínimo para considerar (default: R$ 0,01)
        
        Returns:
            DataFrame filtrado com processos com pagamento excessivo
        """
        if resumo_df.empty:
            return pd.DataFrame()
        
        return resumo_df[resumo_df['SALDO_FINAL_RECONCILIACAO'] < -threshold].copy()
    
    def validate_reconciliation_data(self, detalhada_df: pd.DataFrame, 
                                    resumo_df: pd.DataFrame) -> Dict[str, bool]:
        """
        Valida consistência dos dados de reconciliação.
        
        Verifica:
        - Soma de detalhadas por processo == resumo
        - Todos os processos no resumo têm linhas detalhadas
        - Não há valores NaN/infinitos
        
        Args:
            detalhada_df: DataFrame detalhado
            resumo_df: DataFrame de resumo
        
        Returns:
            Dicionário com resultados de validação:
            {
                'somas_consistentes': bool,
                'todos_processos_tem_detalhes': bool,
                'sem_valores_invalidos': bool,
                'validacao_ok': bool
            }
        """
        validacao = {
            'somas_consistentes': True,
            'todos_processos_tem_detalhes': True,
            'sem_valores_invalidos': True,
            'validacao_ok': True
        }
        
        if resumo_df.empty:
            return validacao
        
        # 1. Verificar somas
        if not detalhada_df.empty:
            soma_detalhada = detalhada_df.groupby('processo')['comissao_calculada'].sum()
            
            for _, row in resumo_df.iterrows():
                processo = row['PROCESSO']
                comissao_resumo = row['COMISSAO_CORRETA_TOTAL']
                comissao_det = soma_detalhada.get(processo, 0.0)
                
                if abs(comissao_resumo - comissao_det) > 0.01:  # tolerance 1 centavo
                    validacao['somas_consistentes'] = False
                    print(f"[Validação] Inconsistência em {processo}: Resumo={comissao_resumo:.2f}, Detalhada={comissao_det:.2f}")
        
        # 2. Verificar se todos têm detalhes
        if not detalhada_df.empty:
            processos_resumo = set(resumo_df['PROCESSO'].tolist())
            processos_detalhada = set(detalhada_df['processo'].unique().tolist())
            
            if processos_resumo != processos_detalhada:
                validacao['todos_processos_tem_detalhes'] = False
                print(f"[Validação] Processos sem detalhes: {processos_resumo - processos_detalhada}")
        
        # 3. Verificar valores inválidos
        for col in ['COMISSAO_CORRETA_TOTAL', 'TOTAL_ADIANTAMENTOS_PAGOS', 'SALDO_FINAL_RECONCILIACAO']:
            if resumo_df[col].isna().any() or resumo_df[col].isin([float('inf'), float('-inf')]).any():
                validacao['sem_valores_invalidos'] = False
                print(f"[Validação] Valores inválidos em coluna {col}")
        
        # 4. Resultado geral
        validacao['validacao_ok'] = all([
            validacao['somas_consistentes'],
            validacao['todos_processos_tem_detalhes'],
            validacao['sem_valores_invalidos']
        ])
        
        return validacao

