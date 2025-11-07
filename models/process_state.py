"""
Gerenciamento do estado de processos.

Este módulo fornece uma interface centralizada para gerenciar o estado dos processos
(ESTADO) que rastreia recebimentos, adiantamentos, reconciliações e status de pagamento.
"""

import pandas as pd
import os
from datetime import datetime
from typing import Optional, Dict, List
import sys

# Adicionar path para importar utils
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.normalization import normalize_text, normalize_process_id


# Esquema padrão do estado
ESTADO_COLUMNS = [
    'PROCESSO',
    'VALOR_TOTAL_PROCESSO',
    'TOTAL_ANTECIPACOES',
    'TOTAL_PAGAMENTOS_REGULARES',
    'TOTAL_PAGO_ACUMULADO',
    'TOTAL_ADIANTADO_COMISSAO',
    'STATUS_PAGAMENTO',
    'STATUS_RECONCILIACAO',
    'STATUS_PROCESSO_ANALISE',
    # Novas colunas para a nova lógica de recebimentos/reconciliação
    'STATUS_CALCULO_MEDIAS',       # PENDENTE | REALIZADO
    'MES_ANO_FATURAMENTO',         # YYYY-MM (string)
    'TCMP',                        # JSON string por colaborador
    'FCMP',                        # JSON string por colaborador
    'ULTIMA_ATUALIZACAO',
    # Colunas de debug e depuração
    'LOG_EVENTOS',                 # Log cronológico de eventos (TEXT)
    'FONTE_PAGAMENTOS',           # Nome do arquivo fonte (TEXT)
    'PAGAMENTOS_PROCESSADOS',     # Lista de pagamentos processados (JSON string)
    'DETALHES_CALCULO_METRICAS',  # Detalhes do cálculo TCMP/FCMP (JSON string)
    'DETALHES_CALCULO_RECONCILIACAO'  # Detalhes do cálculo de reconciliação (JSON string)
]


class ProcessStateManager:
    """
    Gerencia o estado persistente dos processos.
    
    O estado rastreia informações como:
    - Valores totais dos processos
    - Total pago acumulado (recebimentos)
    - Total de comissões adiantadas
    - Status de pagamento e reconciliação
    
    Attributes:
        estado: DataFrame com o estado atual
        filepath: Caminho do arquivo Excel de estado
    """
    
    def __init__(self, estado_df: Optional[pd.DataFrame] = None, filepath: str = 'Estado_Processos_Recebimento.xlsx'):
        """
        Inicializa o gerenciador de estado.
        
        Args:
            estado_df: DataFrame inicial (se None, cria vazio)
            filepath: Caminho do arquivo de estado
        """
        self.filepath = filepath
        
        if estado_df is not None and not estado_df.empty:
            self.estado = self._normalize_estado(estado_df)
        else:
            self.estado = self._create_empty_state()
    
    def _create_empty_state(self) -> pd.DataFrame:
        """Cria DataFrame de estado vazio com colunas corretas."""
        return pd.DataFrame(columns=ESTADO_COLUMNS)
    
    def _normalize_estado(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Normaliza DataFrame de estado para garantir colunas e tipos corretos.
        
        Args:
            df: DataFrame a ser normalizado
        
        Returns:
            DataFrame normalizado
        """
        # Adicionar colunas faltantes
        for col in ESTADO_COLUMNS:
            if col not in df.columns:
                df[col] = None
        
        # Selecionar apenas colunas esperadas (na ordem correta)
        df = df[ESTADO_COLUMNS].copy()
        
        # Normalizar tipos numéricos
        for num_col in ['TOTAL_ANTECIPACOES', 'TOTAL_PAGAMENTOS_REGULARES', 'TOTAL_PAGO_ACUMULADO', 'TOTAL_ADIANTADO_COMISSAO', 'VALOR_TOTAL_PROCESSO']:
            df[num_col] = pd.to_numeric(df[num_col], errors='coerce').fillna(0.0)
        
        # Normalizar status (converter nan para None)
        if 'STATUS_PAGAMENTO' in df.columns:
            df['STATUS_PAGAMENTO'] = df['STATUS_PAGAMENTO'].astype(str).replace({'nan': None})
        if 'STATUS_RECONCILIACAO' in df.columns:
            df['STATUS_RECONCILIACAO'] = df['STATUS_RECONCILIACAO'].astype(str).replace({'nan': None})
        if 'STATUS_CALCULO_MEDIAS' in df.columns:
            df['STATUS_CALCULO_MEDIAS'] = df['STATUS_CALCULO_MEDIAS'].astype(str).replace({'nan': None})
        if 'MES_ANO_FATURAMENTO' in df.columns:
            df['MES_ANO_FATURAMENTO'] = df['MES_ANO_FATURAMENTO'].astype(str).replace({'nan': None})
        # Garantir strings para JSONs (ou None)
        for json_col in ['TCMP', 'FCMP', 'PAGAMENTOS_PROCESSADOS', 'DETALHES_CALCULO_METRICAS', 'DETALHES_CALCULO_RECONCILIACAO']:
            if json_col in df.columns:
                df[json_col] = df[json_col].apply(lambda v: None if pd.isna(v) else str(v))
        
        # Garantir strings para colunas de texto (ou None)
        for text_col in ['LOG_EVENTOS', 'FONTE_PAGAMENTOS']:
            if text_col in df.columns:
                df[text_col] = df[text_col].apply(lambda v: None if pd.isna(v) else str(v))
        
        return df
    
    def load_from_file(self, filepath: Optional[str] = None) -> bool:
        """
        Carrega estado de arquivo Excel.
        
        Args:
            filepath: Caminho do arquivo (usa self.filepath se None)
        
        Returns:
            True se carregou com sucesso, False caso contrário
        """
        if filepath is None:
            filepath = self.filepath
        
        if not os.path.exists(filepath):
            self.estado = self._create_empty_state()
            return False
        
        try:
            # Tentar ler planilha 'ESTADO'
            try:
                df_estado = pd.read_excel(filepath, sheet_name='ESTADO')
            except Exception:
                # Fallback: ler primeira planilha
                df_estado = pd.read_excel(filepath)
            
            self.estado = self._normalize_estado(df_estado)
            return True
            
        except Exception as e:
            print(f"[AVISO] Falha ao carregar estado de {filepath}: {e}")
            self.estado = self._create_empty_state()
            return False
    
    def save_to_file(self, filepath: Optional[str] = None) -> bool:
        """
        Salva estado em arquivo Excel.
        
        Args:
            filepath: Caminho do arquivo (usa self.filepath se None)
        
        Returns:
            True se salvou com sucesso, False caso contrário
        """
        if filepath is None:
            filepath = self.filepath
        
        try:
            with pd.ExcelWriter(filepath, engine='openpyxl') as writer:
                self.estado.to_excel(writer, sheet_name='ESTADO', index=False)
            return True
            
        except Exception as e:
            print(f"[AVISO] Falha ao salvar estado em {filepath}: {e}")
            return False
    
    def get_process_state(self, processo_id) -> Optional[Dict]:
        """
        Retorna estado de um processo específico.
        
        Args:
            processo_id: ID do processo (qualquer tipo - será normalizado)
        
        Returns:
            Dicionário com estado do processo, ou None se não encontrado
        """
        proc_normalized = normalize_process_id(processo_id)
        if proc_normalized is None:
            return None
        
        # Buscar no estado
        mask = self.estado['PROCESSO'].astype(str).str.strip() == proc_normalized
        matches = self.estado[mask]
        
        if matches.empty:
            return None
        
        return matches.iloc[0].to_dict()
    
    def process_exists(self, processo_id) -> bool:
        """
        Verifica se processo existe no estado.
        
        Args:
            processo_id: ID do processo
        
        Returns:
            True se existe, False caso contrário
        """
        return self.get_process_state(processo_id) is not None
    
    def update_payment_received(self, processo_id, valor_recebido: float, 
                                valor_total_processo: Optional[float] = None,
                                status_pagamento: Optional[str] = None) -> None:
        """
        Atualiza TOTAL_PAGO_ACUMULADO para um processo.
        
        Se o processo não existir, cria nova entrada. Se existir, incrementa o valor.
        
        Args:
            processo_id: ID do processo
            valor_recebido: Valor recebido nesta atualização
            valor_total_processo: Valor total do processo (opcional)
            status_pagamento: Status do pagamento (opcional)
        """
        proc_normalized = normalize_process_id(processo_id)
        if proc_normalized is None:
            return
        
        # Buscar índice do processo
        mask = self.estado['PROCESSO'].astype(str).str.strip() == proc_normalized
        indices = self.estado[mask].index
        
        if len(indices) == 0:
            # Criar nova entrada
            nova_linha = {
                'PROCESSO': proc_normalized,
                'VALOR_TOTAL_PROCESSO': valor_total_processo if valor_total_processo is not None else 0.0,
                'TOTAL_PAGO_ACUMULADO': float(valor_recebido),
                'TOTAL_ADIANTADO_COMISSAO': 0.0,
                'STATUS_PAGAMENTO': status_pagamento,
                'STATUS_RECONCILIACAO': 'Nao Realizada',
                'STATUS_PROCESSO_ANALISE': None,
                'STATUS_CALCULO_MEDIAS': 'PENDENTE',
                'MES_ANO_FATURAMENTO': None,
                'TCMP': None,
                'FCMP': None,
                'ULTIMA_ATUALIZACAO': datetime.now().isoformat()
            }
            self.estado = pd.concat([self.estado, pd.DataFrame([nova_linha])], ignore_index=True, sort=False)
        else:
            # Atualizar entrada existente
            idx = indices[0]
            
            # Incrementar total pago
            pago_anterior = pd.to_numeric(self.estado.at[idx, 'TOTAL_PAGO_ACUMULADO'], errors='coerce')
            pago_anterior = float(pago_anterior) if not pd.isna(pago_anterior) else 0.0
            self.estado.at[idx, 'TOTAL_PAGO_ACUMULADO'] = pago_anterior + float(valor_recebido)
            
            # Atualizar status de pagamento se fornecido
            if status_pagamento is not None:
                self.estado.at[idx, 'STATUS_PAGAMENTO'] = status_pagamento
            
            # Atualizar valor total se fornecido e se estava vazio
            if valor_total_processo is not None:
                valor_atual = pd.to_numeric(self.estado.at[idx, 'VALOR_TOTAL_PROCESSO'], errors='coerce')
                if pd.isna(valor_atual) or valor_atual == 0.0:
                    self.estado.at[idx, 'VALOR_TOTAL_PROCESSO'] = float(valor_total_processo)
            
            # Atualizar timestamp
            self.estado.at[idx, 'ULTIMA_ATUALIZACAO'] = datetime.now().isoformat()
    
    def update_payment_advanced(self, processo_id, valor_recebido: float,
                                valor_total_processo: Optional[float] = None,
                                status_pagamento: Optional[str] = None) -> None:
        """
        Atualiza TOTAL_ANTECIPACOES para um processo (antecipações).
        
        Se o processo não existir, cria nova entrada. Se existir, incrementa o valor.
        
        Args:
            processo_id: ID do processo
            valor_recebido: Valor da antecipação recebida
            valor_total_processo: Valor total do processo (opcional)
            status_pagamento: Status do pagamento (opcional)
        """
        proc_normalized = normalize_process_id(processo_id)
        if proc_normalized is None:
            return
        
        # Buscar índice do processo
        mask = self.estado['PROCESSO'].astype(str).str.strip() == proc_normalized
        indices = self.estado[mask].index
        
        if len(indices) == 0:
            # Criar nova entrada com todas as colunas (incluindo debug)
            nova_linha = {
                'PROCESSO': proc_normalized,
                'VALOR_TOTAL_PROCESSO': valor_total_processo if valor_total_processo is not None else 0.0,
                'TOTAL_ANTECIPACOES': float(valor_recebido),
                'TOTAL_PAGAMENTOS_REGULARES': 0.0,
                'TOTAL_PAGO_ACUMULADO': float(valor_recebido),
                'TOTAL_ADIANTADO_COMISSAO': 0.0,
                'STATUS_PAGAMENTO': status_pagamento,
                'STATUS_RECONCILIACAO': 'Nao Realizada',
                'STATUS_PROCESSO_ANALISE': None,
                'STATUS_CALCULO_MEDIAS': 'PENDENTE',
                'MES_ANO_FATURAMENTO': None,
                'TCMP': None,
                'FCMP': None,
                'ULTIMA_ATUALIZACAO': datetime.now().isoformat(),
                # Colunas de debug (inicializadas como None)
                'LOG_EVENTOS': None,
                'FONTE_PAGAMENTOS': None,
                'PAGAMENTOS_PROCESSADOS': None,
                'DETALHES_CALCULO_METRICAS': None,
                'DETALHES_CALCULO_RECONCILIACAO': None
            }
            # Garantir que todas as colunas de ESTADO_COLUMNS estejam presentes
            for col in ESTADO_COLUMNS:
                if col not in nova_linha:
                    nova_linha[col] = None
            self.estado = pd.concat([self.estado, pd.DataFrame([nova_linha])], ignore_index=True, sort=False)
        else:
            # Atualizar entrada existente
            idx = indices[0]
            
            # Incrementar total antecipações
            antecipacoes_anterior = pd.to_numeric(self.estado.at[idx, 'TOTAL_ANTECIPACOES'], errors='coerce')
            antecipacoes_anterior = float(antecipacoes_anterior) if not pd.isna(antecipacoes_anterior) else 0.0
            self.estado.at[idx, 'TOTAL_ANTECIPACOES'] = antecipacoes_anterior + float(valor_recebido)
            
            # Recalcular total pago acumulado
            pagtos_regulares = pd.to_numeric(self.estado.at[idx, 'TOTAL_PAGAMENTOS_REGULARES'], errors='coerce')
            pagtos_regulares = float(pagtos_regulares) if not pd.isna(pagtos_regulares) else 0.0
            self.estado.at[idx, 'TOTAL_PAGO_ACUMULADO'] = antecipacoes_anterior + float(valor_recebido) + pagtos_regulares
            
            # Atualizar status de pagamento se fornecido
            if status_pagamento is not None:
                self.estado.at[idx, 'STATUS_PAGAMENTO'] = str(status_pagamento)
            
            # Atualizar valor total se fornecido e se estava vazio
            if valor_total_processo is not None:
                valor_atual = pd.to_numeric(self.estado.at[idx, 'VALOR_TOTAL_PROCESSO'], errors='coerce')
                if pd.isna(valor_atual) or valor_atual == 0.0:
                    self.estado.at[idx, 'VALOR_TOTAL_PROCESSO'] = float(valor_total_processo)
            
            # Atualizar timestamp
            self.estado.at[idx, 'ULTIMA_ATUALIZACAO'] = datetime.now().isoformat()
    
    def update_payment_regular(self, processo_id, valor_recebido: float,
                               valor_total_processo: Optional[float] = None,
                               status_pagamento: Optional[str] = None) -> None:
        """
        Atualiza TOTAL_PAGAMENTOS_REGULARES para um processo (pagamentos regulares).
        
        Se o processo não existir, cria nova entrada. Se existir, incrementa o valor.
        
        Args:
            processo_id: ID do processo
            valor_recebido: Valor do pagamento regular recebido
            valor_total_processo: Valor total do processo (opcional)
            status_pagamento: Status do pagamento (opcional)
        """
        proc_normalized = normalize_process_id(processo_id)
        if proc_normalized is None:
            return
        
        # Buscar índice do processo
        mask = self.estado['PROCESSO'].astype(str).str.strip() == proc_normalized
        indices = self.estado[mask].index
        
        if len(indices) == 0:
            # Criar nova entrada com todas as colunas (incluindo debug)
            nova_linha = {
                'PROCESSO': proc_normalized,
                'VALOR_TOTAL_PROCESSO': valor_total_processo if valor_total_processo is not None else 0.0,
                'TOTAL_ANTECIPACOES': 0.0,
                'TOTAL_PAGAMENTOS_REGULARES': float(valor_recebido),
                'TOTAL_PAGO_ACUMULADO': float(valor_recebido),
                'TOTAL_ADIANTADO_COMISSAO': 0.0,
                'STATUS_PAGAMENTO': status_pagamento,
                'STATUS_RECONCILIACAO': 'Nao Realizada',
                'STATUS_PROCESSO_ANALISE': None,
                'STATUS_CALCULO_MEDIAS': 'PENDENTE',
                'MES_ANO_FATURAMENTO': None,
                'TCMP': None,
                'FCMP': None,
                'ULTIMA_ATUALIZACAO': datetime.now().isoformat(),
                # Colunas de debug (inicializadas como None)
                'LOG_EVENTOS': None,
                'FONTE_PAGAMENTOS': None,
                'PAGAMENTOS_PROCESSADOS': None,
                'DETALHES_CALCULO_METRICAS': None,
                'DETALHES_CALCULO_RECONCILIACAO': None
            }
            # Garantir que todas as colunas de ESTADO_COLUMNS estejam presentes
            for col in ESTADO_COLUMNS:
                if col not in nova_linha:
                    nova_linha[col] = None
            self.estado = pd.concat([self.estado, pd.DataFrame([nova_linha])], ignore_index=True, sort=False)
        else:
            # Atualizar entrada existente
            idx = indices[0]
            
            # Incrementar total pagamentos regulares
            pagtos_anterior = pd.to_numeric(self.estado.at[idx, 'TOTAL_PAGAMENTOS_REGULARES'], errors='coerce')
            pagtos_anterior = float(pagtos_anterior) if not pd.isna(pagtos_anterior) else 0.0
            self.estado.at[idx, 'TOTAL_PAGAMENTOS_REGULARES'] = pagtos_anterior + float(valor_recebido)
            
            # Recalcular total pago acumulado
            antecipacoes = pd.to_numeric(self.estado.at[idx, 'TOTAL_ANTECIPACOES'], errors='coerce')
            antecipacoes = float(antecipacoes) if not pd.isna(antecipacoes) else 0.0
            self.estado.at[idx, 'TOTAL_PAGO_ACUMULADO'] = antecipacoes + pagtos_anterior + float(valor_recebido)
            
            # Atualizar status de pagamento se fornecido
            if status_pagamento is not None:
                self.estado.at[idx, 'STATUS_PAGAMENTO'] = str(status_pagamento)
            
            # Atualizar valor total se fornecido e se estava vazio
            if valor_total_processo is not None:
                valor_atual = pd.to_numeric(self.estado.at[idx, 'VALOR_TOTAL_PROCESSO'], errors='coerce')
                if pd.isna(valor_atual) or valor_atual == 0.0:
                    self.estado.at[idx, 'VALOR_TOTAL_PROCESSO'] = float(valor_total_processo)
            
            # Atualizar timestamp
            self.estado.at[idx, 'ULTIMA_ATUALIZACAO'] = datetime.now().isoformat()
    
    def update_commission_advanced(self, processo_id, valor_comissao: float) -> None:
        """
        Incrementa TOTAL_ADIANTADO_COMISSAO para um processo.
        
        Se o processo não existir, cria nova entrada.
        
        Args:
            processo_id: ID do processo
            valor_comissao: Valor da comissão adiantada (será somado ao total)
        """
        proc_normalized = normalize_process_id(processo_id)
        if proc_normalized is None:
            return
        
        # Buscar índice do processo
        mask = self.estado['PROCESSO'].astype(str).str.strip() == proc_normalized
        indices = self.estado[mask].index
        
        if len(indices) == 0:
            # Criar nova entrada
            nova_linha = {
                'PROCESSO': proc_normalized,
                'VALOR_TOTAL_PROCESSO': 0.0,
                'TOTAL_ANTECIPACOES': 0.0,
                'TOTAL_PAGAMENTOS_REGULARES': 0.0,
                'TOTAL_PAGO_ACUMULADO': 0.0,
                'TOTAL_ADIANTADO_COMISSAO': float(valor_comissao),
                'STATUS_PAGAMENTO': None,
                'STATUS_RECONCILIACAO': 'Nao Realizada',
                'STATUS_PROCESSO_ANALISE': None,
                'STATUS_CALCULO_MEDIAS': 'PENDENTE',
                'MES_ANO_FATURAMENTO': None,
                'TCMP': None,
                'FCMP': None,
                'ULTIMA_ATUALIZACAO': datetime.now().isoformat()
            }
            self.estado = pd.concat([self.estado, pd.DataFrame([nova_linha])], ignore_index=True, sort=False)
        else:
            # Incrementar comissão adiantada
            idx = indices[0]
            adiantado_anterior = pd.to_numeric(self.estado.at[idx, 'TOTAL_ADIANTADO_COMISSAO'], errors='coerce')
            adiantado_anterior = float(adiantado_anterior) if not pd.isna(adiantado_anterior) else 0.0
            self.estado.at[idx, 'TOTAL_ADIANTADO_COMISSAO'] = adiantado_anterior + float(valor_comissao)
            self.estado.at[idx, 'ULTIMA_ATUALIZACAO'] = datetime.now().isoformat()
    
    def update_process_status(self, processo_id, 
                             status_processo_analise: Optional[str] = None,
                             status_pagamento: Optional[str] = None) -> None:
        """
        Atualiza status de análise e/ou pagamento de um processo.
        
        Args:
            processo_id: ID do processo
            status_processo_analise: Status do processo na análise (ex: "Faturado")
            status_pagamento: Status do pagamento (ex: "Quitado")
        """
        proc_normalized = normalize_process_id(processo_id)
        if proc_normalized is None:
            return
        
        mask = self.estado['PROCESSO'].astype(str).str.strip() == proc_normalized
        indices = self.estado[mask].index
        
        if len(indices) > 0:
            idx = indices[0]
            
            if status_processo_analise is not None:
                self.estado.at[idx, 'STATUS_PROCESSO_ANALISE'] = str(status_processo_analise)
            
            if status_pagamento is not None:
                self.estado.at[idx, 'STATUS_PAGAMENTO'] = str(status_pagamento)
            
            self.estado.at[idx, 'ULTIMA_ATUALIZACAO'] = datetime.now().isoformat()
    
    def mark_reconciliation_done(self, processo_id) -> None:
        """
        Marca reconciliação como realizada para um processo.
        
        Args:
            processo_id: ID do processo
        """
        proc_normalized = normalize_process_id(processo_id)
        if proc_normalized is None:
            return
        
        mask = self.estado['PROCESSO'].astype(str).str.strip() == proc_normalized
        indices = self.estado[mask].index
        
        if len(indices) > 0:
            idx = indices[0]
            self.estado.at[idx, 'STATUS_RECONCILIACAO'] = 'Realizada'
            self.estado.at[idx, 'ULTIMA_ATUALIZACAO'] = datetime.now().isoformat()
    
    def update_process_metrics(self, processo_id,
                               mes_ano_faturamento: Optional[str],
                               tcmp_por_colaborador: Optional[Dict[str, float]],
                               fcmp_por_colaborador: Optional[Dict[str, float]],
                               status_calculo_medias: Optional[str] = 'REALIZADO') -> None:
        """
        Atualiza as métricas TCMP/FCMP por colaborador para um processo.
        
        Args:
            processo_id: ID do processo
            mes_ano_faturamento: 'YYYY-MM'
            tcmp_por_colaborador: dict {nome_colab: tcmp_float}
            fcmp_por_colaborador: dict {nome_colab: fcmp_float}
            status_calculo_medias: 'PENDENTE' | 'REALIZADO'
        """
        import json
        proc_normalized = normalize_process_id(processo_id)
        if proc_normalized is None:
            return
        
        mask = self.estado['PROCESSO'].astype(str).str.strip() == proc_normalized
        indices = self.estado[mask].index
        
        if len(indices) == 0:
            # Criar base se não existir
            nova_linha = {
                'PROCESSO': proc_normalized,
                'VALOR_TOTAL_PROCESSO': 0.0,
                'TOTAL_ANTECIPACOES': 0.0,
                'TOTAL_PAGAMENTOS_REGULARES': 0.0,
                'TOTAL_PAGO_ACUMULADO': 0.0,
                'TOTAL_ADIANTADO_COMISSAO': 0.0,
                'STATUS_PAGAMENTO': None,
                'STATUS_RECONCILIACAO': 'Nao Realizada',
                'STATUS_PROCESSO_ANALISE': None,
                'STATUS_CALCULO_MEDIAS': status_calculo_medias,
                'MES_ANO_FATURAMENTO': mes_ano_faturamento,
                'TCMP': json.dumps(tcmp_por_colaborador or {}, ensure_ascii=False),
                'FCMP': json.dumps(fcmp_por_colaborador or {}, ensure_ascii=False),
                'ULTIMA_ATUALIZACAO': datetime.now().isoformat()
            }
            self.estado = pd.concat([self.estado, pd.DataFrame([nova_linha])], ignore_index=True, sort=False)
        else:
            idx = indices[0]
            if mes_ano_faturamento is not None:
                self.estado.at[idx, 'MES_ANO_FATURAMENTO'] = mes_ano_faturamento
            if tcmp_por_colaborador is not None:
                self.estado.at[idx, 'TCMP'] = json.dumps(tcmp_por_colaborador, ensure_ascii=False)
            if fcmp_por_colaborador is not None:
                self.estado.at[idx, 'FCMP'] = json.dumps(fcmp_por_colaborador, ensure_ascii=False)
            if status_calculo_medias is not None:
                self.estado.at[idx, 'STATUS_CALCULO_MEDIAS'] = status_calculo_medias
            self.estado.at[idx, 'ULTIMA_ATUALIZACAO'] = datetime.now().isoformat()
    
    def get_process_metrics(self, processo_id) -> Optional[Dict]:
        """
        Retorna métricas TCMP/FCMP por colaborador e metadados de faturamento.
        
        Returns:
            dict com chaves: 'TCMP' (dict), 'FCMP' (dict), 'MES_ANO_FATURAMENTO' (str), 'STATUS_CALCULO_MEDIAS' (str)
        """
        import json
        state = self.get_process_state(processo_id)
        if state is None:
            return None
        try:
            tcmp = json.loads(state.get('TCMP') or '{}')
        except Exception:
            tcmp = {}
        try:
            fcmp = json.loads(state.get('FCMP') or '{}')
        except Exception:
            fcmp = {}
        return {
            'TCMP': tcmp,
            'FCMP': fcmp,
            'MES_ANO_FATURAMENTO': state.get('MES_ANO_FATURAMENTO'),
            'STATUS_CALCULO_MEDIAS': state.get('STATUS_CALCULO_MEDIAS')
        }
    
    def get_eligible_for_reconciliation(self) -> pd.DataFrame:
        """
        Retorna processos elegíveis para reconciliação.
        
        Critérios:
        - STATUS_PAGAMENTO contém 'Quitado'
        - STATUS_PROCESSO_ANALISE == 'Faturado'
        - STATUS_RECONCILIACAO não é 'Realizada' ou 'Concluida'
        
        Returns:
            DataFrame com processos elegíveis
        """
        if self.estado.empty:
            return pd.DataFrame(columns=ESTADO_COLUMNS)
        
        # Normalizar status para comparação
        estado_norm = self.estado.copy()
        estado_norm['_status_pag_norm'] = estado_norm['STATUS_PAGAMENTO'].apply(normalize_text)
        estado_norm['_status_analise_norm'] = estado_norm['STATUS_PROCESSO_ANALISE'].apply(normalize_text)
        estado_norm['_status_reconc_norm'] = estado_norm['STATUS_RECONCILIACAO'].apply(normalize_text)
        
        # Aplicar filtros
        mask_quitado = estado_norm['_status_pag_norm'].str.contains('QUITADO', na=False)
        mask_faturado = estado_norm['_status_analise_norm'] == 'FATURADO'
        mask_nao_reconciliado = ~estado_norm['_status_reconc_norm'].isin(['REALIZADA', 'CONCLUIDA'])
        
        eligible = self.estado[mask_quitado & mask_faturado & mask_nao_reconciliado].copy()
        
        return eligible
    
    def get_process_summary(self) -> Dict:
        """
        Retorna resumo estatístico do estado.
        
        Returns:
            Dicionário com estatísticas
        """
        if self.estado.empty:
            return {
                'total_processos': 0,
                'total_pago': 0.0,
                'total_adiantado': 0.0,
                'processos_quitados': 0,
                'processos_reconciliados': 0,
                'processos_elegiveis_reconciliacao': 0
            }
        
        return {
            'total_processos': len(self.estado),
            'total_pago': float(self.estado['TOTAL_PAGO_ACUMULADO'].sum()),
            'total_adiantado': float(self.estado['TOTAL_ADIANTADO_COMISSAO'].sum()),
            'processos_quitados': int((self.estado['STATUS_PAGAMENTO'].apply(normalize_text).str.contains('QUITADO', na=False)).sum()),
            'processos_reconciliados': int((self.estado['STATUS_RECONCILIACAO'].apply(normalize_text) == 'REALIZADA').sum()),
            'processos_elegiveis_reconciliacao': len(self.get_eligible_for_reconciliation())
        }
    
    def get_dataframe(self) -> pd.DataFrame:
        """
        Retorna o DataFrame de estado (cópia).
        
        Returns:
            Cópia do DataFrame de estado
        """
        return self.estado.copy()

