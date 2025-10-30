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
    Orquestra o processamento completo de pagamentos (antecipações + pagamentos regulares).
    
    Este é o ponto de entrada principal para processar pagamentos,
    coordenando mapper, calculator e atualização de estado.
    
    Attributes:
        pagamentos_df: DataFrame unificado com pagamentos (antecipações + regulares)
        mapper: PaymentMapper para mapear pagamentos
        calculator: PaymentCommissionCalculator para calcular comissões
        state_manager: ProcessStateManager para atualizar estado (opcional)
        status_pagamentos_df: DataFrame com status de pagamentos dos processos (opcional)
        nao_mapeados_nf: DataFrame com documentos não mapeados (para avisos)
    """
    
    def __init__(self,
                 recebimentos_df: pd.DataFrame,
                 analise_comercial_df: pd.DataFrame,
                 commission_calculator: PaymentCommissionCalculator,
                 state_manager=None,
                 status_pagamentos_df: pd.DataFrame = None):
        """
        Inicializa o processador.
        
        Args:
            recebimentos_df: DataFrame UNIFICADO com pagamentos (PROCESSO, DOCUMENTO_NORMALIZADO, 
                             VALOR_RECEBIDO/VALOR_PAGO, DATA_RECEBIMENTO/DATA_PAGAMENTO, 
                             ID_CLIENTE, TIPO_PAGAMENTO, FONTE_ORIGINAL)
            analise_comercial_df: DataFrame com análise comercial completa
            commission_calculator: Calculador de comissões
            state_manager: ProcessStateManager para atualizar estado (opcional)
            status_pagamentos_df: DataFrame com status de pagamentos (colunas: PROCESSO, STATUS_PAGAMENTO)
        """
        self.pagamentos_df = recebimentos_df  # Agora é DataFrame unificado
        self.mapper = PaymentMapper(analise_comercial_df)
        self.calculator = commission_calculator
        self.state_manager = state_manager
        self.status_pagamentos_df = status_pagamentos_df if status_pagamentos_df is not None else pd.DataFrame()
        self.nao_mapeados_nf = pd.DataFrame()  # Para registrar documentos não mapeados
    
    def process_all_payments(self) -> Tuple[pd.DataFrame, List[Dict]]:
        """
        Processa todos os pagamentos (antecipações + pagamentos regulares).
        
        Fluxo:
        1. Separar pagamentos por tipo (Antecipação vs Pagamento Regular)
        2. Para cada pagamento, mapear para processo (via PROCESSO ou NUMERO NF)
        3. Extrair contexto do processo
        4. Calcular comissões
        5. Atualizar estado (se state_manager fornecido)
        6. Retornar DataFrame de comissões e log de mapeamentos
        
        Returns:
            Tupla (comissoes_df, log_mapeamentos):
                - comissoes_df: DataFrame com comissões calculadas
                - log_mapeamentos: Lista de dicts com informações de mapeamento
        """
        if self.pagamentos_df.empty:
            return pd.DataFrame(), []
        
        # Separar por tipo
        antecipacoes = self.pagamentos_df[
            self.pagamentos_df['TIPO_PAGAMENTO'] == 'Antecipação'
        ].copy() if 'TIPO_PAGAMENTO' in self.pagamentos_df.columns else self.pagamentos_df.copy()
        
        pagamentos_regulares = self.pagamentos_df[
            self.pagamentos_df['TIPO_PAGAMENTO'] == 'Pagamento Regular'
        ].copy() if 'TIPO_PAGAMENTO' in self.pagamentos_df.columns else pd.DataFrame()
        
        # Processar antecipações (via PROCESSO)
        comissoes_antecip, log_antecip = self._process_payments_by_process(antecipacoes)
        
        # Processar pagamentos regulares (via NUMERO NF)
        comissoes_pagtos, log_pagtos = self._process_payments_by_nf(pagamentos_regulares)
        
        # Combinar resultados
        comissoes_list = []
        if not comissoes_antecip.empty:
            comissoes_antecip['FONTE_PAGAMENTO'] = 'Antecipação'
            comissoes_list.append(comissoes_antecip)
        if not comissoes_pagtos.empty:
            comissoes_pagtos['FONTE_PAGAMENTO'] = 'Pagamento Regular'
            comissoes_list.append(comissoes_pagtos)
        
        comissoes_df = pd.concat(comissoes_list, ignore_index=True) if comissoes_list else pd.DataFrame()
        log_mapeamentos = log_antecip + log_pagtos
        
        return comissoes_df, log_mapeamentos
    
    def _process_payments_by_process(self, pagamentos_df: pd.DataFrame) -> Tuple[pd.DataFrame, List[Dict]]:
        """
        Processa pagamentos usando a coluna PROCESSO (antecipações).
        
        Args:
            pagamentos_df: DataFrame com pagamentos (deve ter coluna PROCESSO)
        
        Returns:
            Tupla (comissoes_df, log_mapeamentos)
        """
        if pagamentos_df.empty:
            return pd.DataFrame(), []
        
        comissoes_list = []
        log_mapeamentos = []
        
        for _, payment_row in pagamentos_df.iterrows():
            processo = payment_row.get('PROCESSO')
            valor_recebido = payment_row.get('VALOR_RECEBIDO', payment_row.get('VALOR_PAGO'))
            id_cliente = payment_row.get('ID_CLIENTE')
            data_recebimento = payment_row.get('DATA_RECEBIMENTO', payment_row.get('DATA_PAGAMENTO'))
            
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
    
    def _process_payments_by_nf(self, pagamentos_df: pd.DataFrame) -> Tuple[pd.DataFrame, List[Dict]]:
        """
        Processa pagamentos regulares usando NUMERO NF.
        
        Args:
            pagamentos_df: DataFrame com pagamentos regulares (deve ter coluna DOCUMENTO_NORMALIZADO)
        
        Returns:
            Tupla (comissoes_df, log_mapeamentos)
        """
        if pagamentos_df.empty:
            return pd.DataFrame(), []
        
        comissoes_list = []
        log_mapeamentos = []
        nao_mapeados_list = []
        
        for _, payment_row in pagamentos_df.iterrows():
            documento_normalizado = payment_row.get('DOCUMENTO_NORMALIZADO')
            documento_original = payment_row.get('DOCUMENTO_ORIGINAL')
            valor_pago = payment_row.get('VALOR_PAGO')
            id_cliente = payment_row.get('ID_CLIENTE')
            data_pagamento = payment_row.get('DATA_PAGAMENTO')
            
            # Validar dados básicos
            if pd.isna(documento_normalizado) or pd.isna(valor_pago):
                log_mapeamentos.append({
                    'documento': documento_original,
                    'valor_pago': valor_pago,
                    'status': 'DADOS_INVALIDOS',
                    'metodo': None,
                    'comissoes_geradas': 0
                })
                continue
            
            # 1. Mapear pagamento para processo via NUMERO NF
            mapped_row, map_method = self.mapper.map_payment_by_nf(
                documento_normalizado, valor_pago, id_cliente
            )
            
            if mapped_row is None:
                # NÃO ENCONTRADO - Registrar para aviso
                nao_mapeados_list.append({
                    'DOCUMENTO_ORIGINAL': documento_original,
                    'DOCUMENTO_NORMALIZADO': documento_normalizado,
                    'VALOR': valor_pago,
                    'CLIENTE': id_cliente,
                    'DATA': data_pagamento,
                    'MOTIVO': 'Documento não encontrado na Análise Comercial'
                })
                
                log_mapeamentos.append({
                    'documento': documento_original,
                    'valor_pago': valor_pago,
                    'status': 'NAO_MAPEADO',
                    'metodo': map_method,
                    'comissoes_geradas': 0
                })
                continue
            
            # 2. Extrair contexto do processo
            process_context = self.mapper.get_process_context(mapped_row)
            
            # Obter processo do contexto (para atualizar estado)
            processo = process_context.get('processo')
            
            # 3. Calcular comissões para colaboradores que recebem por recebimento
            comissoes = self.calculator.calculate_for_payment(
                processo, valor_pago, process_context
            )
            
            # Adicionar dados adicionais às comissões
            for comissao in comissoes:
                if pd.notna(data_pagamento):
                    comissao['data_recebimento'] = data_pagamento
                comissao['documento_nf'] = documento_original
                comissao['mapping_found'] = True
                comissao['mapping_method'] = map_method
            
            comissoes_list.extend(comissoes)
            
            # 4. Atualizar estado (se fornecido)
            if self.state_manager is not None and processo:
                self._update_state_for_payment(
                    processo, 
                    valor_pago, 
                    comissoes, 
                    process_context,
                    tipo_pagamento='Pagamento Regular'
                )
            
            # Log de mapeamento
            log_mapeamentos.append({
                'documento': documento_original,
                'processo': processo,
                'valor_pago': valor_pago,
                'status': 'MAPEADO',
                'metodo': map_method,
                'linha': process_context.get('linha'),
                'comissoes_geradas': len(comissoes)
            })
        
        # Armazenar não mapeados para relatório
        self.nao_mapeados_nf = pd.DataFrame(nao_mapeados_list)
        
        # Converter lista para DataFrame
        comissoes_df = pd.DataFrame(comissoes_list) if comissoes_list else pd.DataFrame()
        
        return comissoes_df, log_mapeamentos
    
    def _update_state_for_payment(self, processo: str, valor_recebido: float,
                                  comissoes: List[Dict], process_context: Dict,
                                  tipo_pagamento: str = 'Antecipação') -> None:
        """
        Atualiza estado para um pagamento processado.
        
        Args:
            processo: ID do processo
            valor_recebido: Valor recebido/pago
            comissoes: Lista de comissões calculadas
            process_context: Contexto do processo
            tipo_pagamento: 'Antecipação' ou 'Pagamento Regular'
        """
        if self.state_manager is None:
            return
        
        # Buscar STATUS_PAGAMENTO do arquivo Status_Pagamentos_Processos
        status_pagamento = None
        if not self.status_pagamentos_df.empty:
            try:
                # Normalizar processo para busca
                from utils.normalization import normalize_process_id
                proc_norm = normalize_process_id(processo)
                
                # Buscar status
                mask = self.status_pagamentos_df['PROCESSO'].astype(str).str.strip() == proc_norm
                matches = self.status_pagamentos_df[mask]
                
                if not matches.empty:
                    status_pagamento = matches.iloc[0].get('STATUS_PAGAMENTO')
            except Exception:
                pass
        
        # Atualizar valor pago acumulado (separado por tipo)
        valor_total_processo = process_context.get('valor_processo')
        
        if tipo_pagamento == 'Antecipação':
            self.state_manager.update_payment_advanced(
                processo,
                valor_recebido,
                valor_total_processo=valor_total_processo,
                status_pagamento=status_pagamento
            )
        else:  # Pagamento Regular
            self.state_manager.update_payment_regular(
                processo,
                valor_recebido,
                valor_total_processo=valor_total_processo,
                status_pagamento=status_pagamento
            )
        
        # Atualizar comissão adiantada acumulada
        total_comissao = sum(c.get('comissao_calculada', 0.0) for c in comissoes)
        if total_comissao > 0:
            self.state_manager.update_commission_advanced(processo, total_comissao)
        
        # Atualizar STATUS_PROCESSO_ANALISE (ex: "Faturado")
        status_processo_analise = process_context.get('status_processo')
        if status_processo_analise is not None or status_pagamento is not None:
            self.state_manager.update_process_status(
                processo,
                status_processo_analise=status_processo_analise,
                status_pagamento=status_pagamento
            )
    
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

