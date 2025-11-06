"""
Cálculo de métricas por processo (TCMP e FCMP) por colaborador.

TCMP (Taxa de Comissão Média Ponderada):
  - Média ponderada por valor do item das taxas por item:
    taxa_item = taxa_rateio_maximo_pct * fatia_cargo_pct (em decimal)

FCMP (Fator de Correção Médio Ponderado):
  - Média ponderada por valor do item dos FCs calculados por item

Uso:
  calculator = ProcessMetricsCalculator(...)
  tcmp_dict, fcmp_dict = calculator.calculate_for_process('123456')
"""

import sys
import os
from typing import Dict, Tuple, Optional, List
import pandas as pd

# Adicionar path para imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.column_finder import ColumnFinder


class ProcessMetricsCalculator:
    """Calcula TCMP e FCMP por colaborador para um processo."""

    def __init__(
        self,
        analise_comercial_df: pd.DataFrame,
        regras_comissao_getter,
        fc_calculator_func,
        colaboradores_df: pd.DataFrame,
        atribuicoes_df: pd.DataFrame,
        recebe_por_recebimento_ids: set,
    ) -> None:
        self.analise_df = analise_comercial_df if analise_comercial_df is not None and not analise_comercial_df.empty else pd.DataFrame()
        self.get_regra = regras_comissao_getter
        self.calculate_fc_item = fc_calculator_func
        self.colaboradores_df = colaboradores_df if colaboradores_df is not None and not colaboradores_df.empty else pd.DataFrame()
        self.atribuicoes_df = atribuicoes_df if atribuicoes_df is not None and not atribuicoes_df.empty else pd.DataFrame()
        self.recebe_por_recebimento_ids = {str(n).strip().upper() for n in (recebe_por_recebimento_ids or set())}

    def calculate_for_process(self, processo_id: str) -> Tuple[Dict[str, float], Dict[str, float]]:
        """
        Calcula TCMP e FCMP por colaborador para um processo.

        Args:
            processo_id: ID do processo

        Returns:
            (tcmp_por_colab, fcmp_por_colab)
        """
        itens = self._get_process_items(processo_id)
        if itens.empty:
            return {}, {}

        # Índices por colaborador
        contrib_taxa: Dict[str, float] = {}
        contrib_fc: Dict[str, float] = {}
        soma_valores: Dict[str, float] = {}

        for _, item in itens.iterrows():
            contexto = self._extract_item_context(item)
            valor_item = contexto.get('valor_realizado', 0.0) or 0.0
            if valor_item == 0:
                continue

            # Colaboradores relevantes (somente quem recebe por recebimento)
            colaboradores = self._get_colaboradores_recebimento(contexto)
            for colab in colaboradores:
                nome = colab['nome']
                cargo = colab['cargo']
                chave = nome  # por nome canônico

                # Regra por item/colaborador
                regra = self.get_regra(
                    contexto['linha'], contexto['grupo'], contexto['subgrupo'], contexto['tipo_mercadoria'], cargo
                )
                if regra is None:
                    continue

                try:
                    taxa_rateio = float(regra.get('taxa_rateio_maximo_pct', 0.0)) / 100.0
                    pe = float(regra.get('fatia_cargo_pct', 0.0)) / 100.0
                except (TypeError, ValueError):
                    taxa_rateio, pe = 0.0, 0.0

                taxa_item = taxa_rateio * pe

                # FC por item para o colaborador (usa lógica já existente)
                fc_item_val = 0.0
                try:
                    fc_val, _detalhes = self.calculate_fc_item(
                        nome, cargo, item, None, None, None
                    )
                    # calculate_fc_item pode retornar (fc, detalhes) ou dict {'fc_final': ...}
                    if isinstance(fc_val, dict):
                        fc_item_val = float(fc_val.get('fc_final', 0.0))
                    elif isinstance(fc_val, (int, float)):
                        fc_item_val = float(fc_val)
                    else:
                        fc_item_val = 0.0
                except Exception:
                    fc_item_val = 0.0

                # Acumular ponderações
                contrib_taxa[chave] = contrib_taxa.get(chave, 0.0) + taxa_item * valor_item
                contrib_fc[chave] = contrib_fc.get(chave, 0.0) + fc_item_val * valor_item
                soma_valores[chave] = soma_valores.get(chave, 0.0) + valor_item

        # Finalizar médias ponderadas
        tcmp_por_colab = {
            colab: (contrib_taxa[colab] / soma_valores[colab]) if soma_valores[colab] > 0 else 0.0
            for colab in contrib_taxa.keys()
        }
        fcmp_por_colab = {
            colab: (contrib_fc[colab] / soma_valores[colab]) if soma_valores[colab] > 0 else 0.0
            for colab in contrib_fc.keys()
        }
        return tcmp_por_colab, fcmp_por_colab

    # --------- Helpers ---------
    def _get_process_items(self, processo_id: str) -> pd.DataFrame:
        if self.analise_df.empty:
            return pd.DataFrame()
        finder = ColumnFinder(self.analise_df)
        proc_col = finder.find_column(['processo', 'id processo'])
        if not proc_col:
            return pd.DataFrame()
        proc_str = str(processo_id).strip()
        mask = self.analise_df[proc_col].astype(str).str.strip() == proc_str
        itens = self.analise_df[mask].copy()
        if itens.empty:
            # tentar como inteiro
            try:
                proc_int = str(int(float(proc_str)))
                mask = self.analise_df[proc_col].astype(str).str.strip() == proc_int
                itens = self.analise_df[mask].copy()
            except Exception:
                pass
        return itens

    def _extract_item_context(self, item: pd.Series) -> Dict:
        temp_df = pd.DataFrame([item])
        finder = ColumnFinder(temp_df)

        def get_value(aliases: List[str]):
            col = finder.find_column(aliases)
            if col:
                val = item.get(col)
                return str(val).strip() if pd.notna(val) else None
            return None

        def get_numeric(aliases: List[str]):
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
            'valor_realizado': get_numeric(['valor realizado', 'valor_realizado', 'faturamento']),
            'consultor_interno': get_value(['consultor interno', 'consultorinterno']),
            'representante': get_value(['representante-pedido', 'representante']),
        }

    def _get_colaboradores_recebimento(self, contexto: Dict) -> List[Dict]:
        """Busca colaboradores (gestão + operacional) para contexto que recebem por recebimento."""
        colaboradores = []
        vistos = set()

        # Gestão via atribuições
        if not self.atribuicoes_df.empty and not self.colaboradores_df.empty:
            try:
                cargos_gestao = self.colaboradores_df[
                    self.colaboradores_df['tipo_cargo'] == 'Gestão'
                ]['cargo'].unique()
                atribuicoes_gestao = self.atribuicoes_df[
                    self.atribuicoes_df['cargo'].isin(cargos_gestao)
                ]
                mask = (
                    (atribuicoes_gestao['linha'] == contexto.get('linha')) &
                    (atribuicoes_gestao['grupo'] == contexto.get('grupo')) &
                    (atribuicoes_gestao['subgrupo'] == contexto.get('subgrupo')) &
                    (atribuicoes_gestao['tipo_mercadoria'] == contexto.get('tipo_mercadoria'))
                )
                atribuidos = atribuicoes_gestao[mask]
                for _, atr in atribuidos.iterrows():
                    nome = str(atr.get('colaborador')).strip()
                    cargo = atr.get('cargo')
                    if not nome:
                        continue
                    if nome.upper() in vistos:
                        continue
                    vistos.add(nome.upper())
                    colaboradores.append({
                        'nome': nome,
                        'cargo': cargo
                    })
            except Exception:
                pass

        # Operacional (consultor e representante)
        for nome in [contexto.get('consultor_interno'), contexto.get('representante')]:
            if nome and isinstance(nome, str):
                nome_norm = nome.strip().upper()
                if nome_norm not in vistos:
                    # Buscar cargo no df de colaboradores
                    cargo = None
                    row = self.colaboradores_df[self.colaboradores_df['nome_colaborador'] == nome]
                    if not row.empty:
                        cargo = row.iloc[0].get('cargo')
                    colaboradores.append({'nome': nome.strip(), 'cargo': cargo})
                    vistos.add(nome_norm)

        # Filtrar somente quem recebe por recebimento
        return [c for c in colaboradores if str(c['nome']).strip().upper() in self.recebe_por_recebimento_ids]


