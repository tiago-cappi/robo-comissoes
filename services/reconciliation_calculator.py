"""
Cálculo de reconciliação retroativa de comissões.

Este módulo recalcula comissões usando dados históricos do mês de faturamento,
corrigindo as comissões adiantadas por recebimento com base no desempenho real.
"""

import pandas as pd
import sys
import os
from typing import List, Dict, Tuple, Optional
from datetime import datetime

# Adicionar path para imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.column_finder import ColumnFinder
from utils.date_parser import parse_date_flexible, extract_year_month
from .historical_data_loader import HistoricalDataLoader
from .realized_metrics_builder import RealizedMetricsBuilder


class ReconciliationCalculator:
    """
    Calcula reconciliação retroativa para processos quitados.
    
    A reconciliação recalcula comissões item a item usando:
    - Dados históricos do mês de faturamento do processo
    - FC (Fator de Correção) calculado com realizados históricos
    - Mesma lógica de cálculo, mas com dados corretos
    
    Attributes:
        analise_df: DataFrame com análise comercial completa
        historical_loader: HistoricalDataLoader para carregar dados históricos
        metrics_builder: RealizedMetricsBuilder para construir séries
        fc_calculator: Função que calcula FC
        regras_comissao_getter: Função que retorna regras de comissão
        colaboradores_df: DataFrame com colaboradores
        atribuicoes_df: DataFrame com atribuições
        recebe_por_recebimento_ids: Set com quem recebe por recebimento
    """
    
    def __init__(self,
                 analise_comercial_df: pd.DataFrame,
                 fc_calculator_func,
                 regras_comissao_getter,
                 colaboradores_df: pd.DataFrame,
                 atribuicoes_df: pd.DataFrame,
                 recebe_por_recebimento_ids: set,
                 base_path: str = None):
        """
        Inicializa o calculador.
        
        Args:
            analise_comercial_df: DataFrame com análise comercial completa
            fc_calculator_func: Função que calcula FC: func(nome, cargo, item, realizados, mes, ano) -> dict
            regras_comissao_getter: Função que retorna regra: func(linha, grupo, subgrupo, tipo, cargo) -> dict
            colaboradores_df: DataFrame com colaboradores
            atribuicoes_df: DataFrame com atribuições
            recebe_por_recebimento_ids: Set com nomes de quem recebe por recebimento
            base_path: Caminho base do projeto
        """
        self.analise_df = analise_comercial_df
        self.calculate_fc = fc_calculator_func
        self.get_regra_comissao = regras_comissao_getter
        self.colaboradores_df = colaboradores_df
        self.atribuicoes_df = atribuicoes_df
        self.recebe_por_recebimento_ids = recebe_por_recebimento_ids
        
        # Serviços auxiliares
        self.historical_loader = HistoricalDataLoader(base_path)
        self.metrics_builder = RealizedMetricsBuilder()
    
    def reconcile_process(self, processo_id: str) -> Tuple[List[Dict], float]:
        """
        Executa reconciliação para um processo específico.
        
        Fluxo:
        1. Buscar itens do processo na análise comercial
        2. Identificar mês/ano de emissão
        3. Carregar dados históricos do mês
        4. Construir séries de realizados históricos
        5. Recalcular comissões item a item com FC histórico
        
        Args:
            processo_id: ID do processo
        
        Returns:
            Tupla (linhas_detalhadas, comissao_correta_total):
                - linhas_detalhadas: Lista de dicts com comissões calculadas
                - comissao_correta_total: Soma total das comissões
        """
        # 1. Buscar itens do processo
        itens_processo = self._get_process_items(processo_id)
        
        if itens_processo.empty:
            print(f"[Reconc-Info] Processo {processo_id} não encontrado na análise comercial")
            return [], 0.0
        
        # 2. Identificar mês/ano de emissão
        data_emissao = self._extract_emission_date(itens_processo)
        
        if pd.isna(data_emissao):
            print(f"[Reconc-Erro] Não foi possível ler data de emissão para {processo_id}")
            return [], 0.0
        
        mes_fat, ano_fat = data_emissao.month, data_emissao.year
        print(f"[Reconc-Info] Processando {processo_id} para {mes_fat:02d}/{ano_fat}")
        
        # 3. Carregar dados históricos
        try:
            historical_data = self.historical_loader.load_for_month(mes_fat, ano_fat)
        except Exception as e:
            print(f"[Reconc-Erro] Falha ao carregar dados históricos: {e}")
            return [], 0.0
        
        # 4. Construir séries de realizados históricos
        realizados_historicos = self.metrics_builder.build_from_dataframes(
            historical_data['faturados'],
            historical_data['conversoes'],
            historical_data['rentabilidade']
        )
        
        # 5. Recalcular comissões item a item
        linhas_detalhadas = []
        
        for _, item in itens_processo.iterrows():
            # Identificar colaboradores que recebem por recebimento
            colaboradores = self._get_payment_receivers_for_item(item)
            
            for colab in colaboradores:
                # Extrair contexto do item
                contexto = self._extract_item_context(item)
                
                # Buscar regra de comissão
                regra = self.get_regra_comissao(
                    contexto['linha'],
                    contexto['grupo'],
                    contexto['subgrupo'],
                    contexto['tipo_mercadoria'],
                    colab['cargo']
                )
                
                if regra is None:
                    continue
                
                # Calcular FC usando dados históricos
                fc_result = self.calculate_fc(
                    colab['nome'],
                    colab['cargo'],
                    item,
                    realizados_historicos,  # CHAVE: usar histórico!
                    mes_fat,
                    ano_fat
                )
                
                # Extrair FC e detalhes
                fc_final = fc_result.get('fc_final', 0.0) if isinstance(fc_result, dict) else 0.0
                fc_detalhes = fc_result if isinstance(fc_result, dict) else {}
                
                # Calcular comissão com FC histórico
                try:
                    taxa_rateio = float(regra.get('taxa_rateio_maximo_pct', 0)) / 100.0
                    pe = float(regra.get('fatia_cargo_pct', 0)) / 100.0
                    valor_item = float(contexto.get('valor_realizado', 0))
                except (ValueError, TypeError):
                    taxa_rateio = 0.0
                    pe = 0.0
                    valor_item = 0.0
                
                comissao_potencial = valor_item * taxa_rateio * pe
                comissao_calculada = comissao_potencial * fc_final
                
                # Montar linha detalhada (ordem compatível com COMISSOES_CALCULADAS)
                # Ordem: id, nome, cargo, processo, cod_produto, desc, linha, grupo, subgrupo, tipo_merc,
                #        fat_item, taxa_rateio, pe, fc, [detalhes_fc...], comissao_pot, comissao_calc
                linha = {
                    'id_colaborador': colab.get('id_colaborador'),
                    'nome_colaborador': colab['nome'],
                    'cargo': colab['cargo'],
                    'processo': processo_id,
                    'cod_produto': contexto.get('cod_produto'),
                    'descricao_produto': contexto.get('descricao_produto'),
                    'linha': contexto['linha'],
                    'grupo': contexto['grupo'],
                    'subgrupo': contexto['subgrupo'],
                    'tipo_mercadoria': contexto['tipo_mercadoria'],
                    'faturamento_item': valor_item,
                    'taxa_rateio_aplicada': taxa_rateio,
                    'percentual_elegibilidade_pe': pe,
                    'fator_correcao_fc': fc_final
                }
                
                # Expandir detalhes do FC em colunas separadas (mesmo formato de COMISSOES_CALCULADAS)
                mapping = {
                    'faturamento_linha': 'fat_linha',
                    'conversao_linha': 'conv_linha',
                    'faturamento_individual': 'fat_ind',
                    'conversao_individual': 'conv_ind',
                    'rentabilidade': 'rentab',
                    'retencao_clientes': 'retencao',
                    'meta_fornecedor_1': 'forn1',
                    'meta_fornecedor_2': 'forn2'
                }
                
                for comp, short in mapping.items():
                    detalhes = fc_detalhes.get(comp) if isinstance(fc_detalhes, dict) else None
                    if detalhes and isinstance(detalhes, dict):
                        linha[f'peso_{short}'] = detalhes.get('peso', None)
                        linha[f'realizado_{short}'] = detalhes.get('realizado', None)
                        linha[f'meta_{short}'] = detalhes.get('meta', None)
                        linha[f'ating_{short}'] = detalhes.get('atingimento', None)
                        linha[f'ating_cap_{short}'] = detalhes.get('atingimento_cap', None)
                        linha[f'comp_fc_{short}'] = detalhes.get('componente_fc', None)
                        # Para fornecedores, incluir moeda
                        if comp.startswith('meta_fornecedor'):
                            linha[f'moeda_{short}'] = detalhes.get('moeda', None)
                    else:
                        # Se não houver detalhes, preencher com None
                        linha[f'peso_{short}'] = None
                        linha[f'realizado_{short}'] = None
                        linha[f'meta_{short}'] = None
                        linha[f'ating_{short}'] = None
                        linha[f'ating_cap_{short}'] = None
                        linha[f'comp_fc_{short}'] = None
                        if comp.startswith('meta_fornecedor'):
                            linha[f'moeda_{short}'] = None
                
                # Adicionar colunas finais (após os detalhes do FC)
                linha['comissao_potencial_maxima'] = comissao_potencial
                linha['comissao_calculada'] = comissao_calculada
                
                linhas_detalhadas.append(linha)
        
        # Calcular total
        comissao_correta_total = sum(l['comissao_calculada'] for l in linhas_detalhadas)
        
        return linhas_detalhadas, comissao_correta_total
    
    def _get_process_items(self, processo_id: str) -> pd.DataFrame:
        """
        Busca itens do processo na análise comercial.
        
        Args:
            processo_id: ID do processo
        
        Returns:
            DataFrame com itens do processo
        """
        if self.analise_df.empty:
            return pd.DataFrame()
        
        finder = ColumnFinder(self.analise_df)
        proc_col = finder.find_column(['processo', 'id processo'])
        
        if proc_col is None:
            return pd.DataFrame()
        
        # Normalizar para comparação
        proc_str = str(processo_id).strip()
        mask = self.analise_df[proc_col].astype(str).str.strip() == proc_str
        itens = self.analise_df[mask].copy()
        
        # Fallback: tentar como inteiro
        if itens.empty:
            try:
                proc_int = str(int(float(proc_str)))
                mask = self.analise_df[proc_col].astype(str).str.strip() == proc_int
                itens = self.analise_df[mask].copy()
            except Exception:
                pass
        
        return itens
    
    def _extract_emission_date(self, itens_df: pd.DataFrame) -> Optional[pd.Timestamp]:
        """
        Extrai data de emissão dos itens do processo.
        
        Args:
            itens_df: DataFrame com itens
        
        Returns:
            pd.Timestamp com data de emissão, ou None
        """
        if itens_df.empty:
            return None
        
        finder = ColumnFinder(itens_df)
        data_col = finder.find_column(['dt emissão', 'dt emissao', 'data emissão', 'data emissao'])
        
        if data_col is None:
            return None
        
        data_valor = itens_df[data_col].iloc[0]
        return parse_date_flexible(data_valor)
    
    def _extract_item_context(self, item: pd.Series) -> Dict:
        """
        Extrai contexto do item (linha, grupo, subgrupo, tipo, valor, etc).
        
        Args:
            item: Série com dados do item
        
        Returns:
            Dicionário com contexto
        """
        # Criar DataFrame temporário para usar ColumnFinder
        temp_df = pd.DataFrame([item])
        finder = ColumnFinder(temp_df)
        
        def get_value(aliases: list):
            col = finder.find_column(aliases)
            if col:
                val = item.get(col)
                return str(val).strip() if pd.notna(val) else None
            return None
        
        def get_numeric(aliases: list):
            col = finder.find_column(aliases)
            if col:
                try:
                    return float(item.get(col))
                except (ValueError, TypeError):
                    return 0.0
            return 0.0
        
        return {
            'linha': get_value(['negocio', 'negócio', 'linha']),
            'grupo': get_value(['grupo']),
            'subgrupo': get_value(['subgrupo']),
            'tipo_mercadoria': get_value(['tipo de mercadoria', 'tipo mercadoria']),
            'cod_produto': get_value(['código produto', 'codigo produto', 'cod_produto']),
            'descricao_produto': get_value(['descrição produto', 'descricao produto']),
            'valor_realizado': get_numeric(['valor realizado', 'valor_realizado', 'faturamento']),
            'consultor_interno': get_value(['consultor interno', 'consultorinterno']),
            'representante': get_value(['representante-pedido', 'representante'])
        }
    
    def _get_payment_receivers_for_item(self, item: pd.Series) -> List[Dict]:
        """
        Identifica colaboradores que recebem por recebimento no item.
        
        Similar à lógica de PaymentCommissionCalculator, mas opera em item ao invés de contexto.
        
        Args:
            item: Série com dados do item
        
        Returns:
            Lista de dicts com colaboradores
        """
        contexto = self._extract_item_context(item)
        colaboradores = []
        colaboradores_nomes = set()
        
        # 1. Gestão por atribuições
        gestao = self._get_gestao_colaboradores_for_context(contexto)
        for colab in gestao:
            nome_norm = str(colab['nome']).strip().upper()
            if nome_norm not in colaboradores_nomes:
                colaboradores.append(colab)
                colaboradores_nomes.add(nome_norm)
        
        # 2. Operacional (consultor e representante)
        operacional = self._get_operacional_colaboradores_for_context(contexto)
        for colab in operacional:
            nome_norm = str(colab['nome']).strip().upper()
            if nome_norm not in colaboradores_nomes:
                colaboradores.append(colab)
                colaboradores_nomes.add(nome_norm)
        
        # Filtrar apenas quem recebe por recebimento
        recebe_set_norm = {str(n).strip().upper() for n in self.recebe_por_recebimento_ids}
        return [c for c in colaboradores if str(c['nome']).strip().upper() in recebe_set_norm]
    
    def _get_gestao_colaboradores_for_context(self, contexto: Dict) -> List[Dict]:
        """Busca colaboradores de gestão por atribuições."""
        if self.atribuicoes_df.empty or self.colaboradores_df.empty:
            return []
        
        try:
            # Filtrar cargos de gestão
            cargos_gestao = self.colaboradores_df[
                self.colaboradores_df['tipo_cargo'] == 'Gestão'
            ]['cargo'].unique()
            
            atribuicoes_gestao = self.atribuicoes_df[
                self.atribuicoes_df['cargo'].isin(cargos_gestao)
            ]
            
            if atribuicoes_gestao.empty:
                return []
            
            # Buscar por contexto
            mask = (
                (atribuicoes_gestao['linha'] == contexto.get('linha')) &
                (atribuicoes_gestao['grupo'] == contexto.get('grupo')) &
                (atribuicoes_gestao['subgrupo'] == contexto.get('subgrupo')) &
                (atribuicoes_gestao['tipo_mercadoria'] == contexto.get('tipo_mercadoria'))
            )
            
            atribuidos = atribuicoes_gestao[mask]
            
            colaboradores = []
            for _, atr in atribuidos.iterrows():
                nome = atr.get('colaborador')
                cargo = atr.get('cargo')
                
                # Buscar id_colaborador
                colab_row = self.colaboradores_df[
                    self.colaboradores_df['nome_colaborador'] == nome
                ]
                id_colab = colab_row.iloc[0]['id_colaborador'] if not colab_row.empty else None
                
                colaboradores.append({
                    'nome': nome,
                    'cargo': cargo,
                    'id_colaborador': id_colab
                })
            
            return colaboradores
        except Exception:
            return []
    
    def _get_operacional_colaboradores_for_context(self, contexto: Dict) -> List[Dict]:
        """Busca colaboradores operacionais (consultor e representante)."""
        if self.colaboradores_df.empty:
            return []
        
        nomes = []
        
        consultor = contexto.get('consultor_interno')
        if consultor and pd.notna(consultor):
            nomes.append(str(consultor).strip())
        
        representante = contexto.get('representante')
        if representante and pd.notna(representante):
            nomes.append(str(representante).strip())
        
        if not nomes:
            return []
        
        colaboradores = []
        for nome in nomes:
            colab_row = self.colaboradores_df[
                self.colaboradores_df['nome_colaborador'] == nome
            ]
            
            if not colab_row.empty:
                colaboradores.append({
                    'nome': nome,
                    'cargo': colab_row.iloc[0]['cargo'],
                    'id_colaborador': colab_row.iloc[0]['id_colaborador']
                })
        
        return colaboradores

