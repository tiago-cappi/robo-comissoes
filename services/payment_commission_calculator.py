"""
Cálculo de comissões por recebimento.

Este módulo calcula comissões para colaboradores que recebem por recebimento
(ao invés de por faturamento), aplicando a fórmula:
comissao = valor_recebido * taxa_rateio * percentual_elegibilidade
"""

import pandas as pd
import sys
import os
from typing import List, Dict, Set, Optional

# Adicionar path para importar utils
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.normalization import normalize_text


class PaymentCommissionCalculator:
    """
    Calcula comissões para colaboradores que recebem por recebimento.

    O cálculo é mais simples que por faturamento:
    - FC (Fator de Correção) = 1.0 sempre
    - Fórmula: valor_recebido * taxa_rateio * PE

    Attributes:
        regras_comissao: Callable que retorna regra de comissão
        colaboradores_df: DataFrame com colaboradores e cargos
        atribuicoes_df: DataFrame com atribuições de gestão
        recebe_por_recebimento_ids: Set com IDs/nomes de quem recebe por recebimento
    """

    def __init__(
        self,
        regras_comissao_getter,
        colaboradores_df: pd.DataFrame,
        atribuicoes_df: pd.DataFrame,
        recebe_por_recebimento_ids: Set[str],
    ):
        """
        Inicializa o calculador.

        Args:
            regras_comissao_getter: Função que retorna regra: func(linha, grupo, subgrupo, tipo, cargo) -> dict
            colaboradores_df: DataFrame com colaboradores (colunas: id_colaborador, nome_colaborador, cargo, tipo_cargo)
            atribuicoes_df: DataFrame com atribuições (colunas: colaborador, cargo, linha, grupo, subgrupo, tipo_mercadoria)
            recebe_por_recebimento_ids: Set com nomes de colaboradores que recebem por recebimento
        """
        self.get_regra_comissao = regras_comissao_getter
        self.colaboradores_df = colaboradores_df
        self.atribuicoes_df = atribuicoes_df
        self.recebe_por_recebimento_ids = recebe_por_recebimento_ids

        # Normalizar nomes para comparação case-insensitive
        self.recebe_por_recebimento_norm = {
            normalize_text(nome) for nome in recebe_por_recebimento_ids
        }

    def calculate_for_payment(
        self, processo: str, valor_recebido: float, process_context: Dict
    ) -> List[Dict]:
        """
        Calcula comissões de um recebimento específico.

        Args:
            processo: ID do processo
            valor_recebido: Valor recebido
            process_context: Contexto do processo (linha, grupo, subgrupo, tipo_mercadoria, consultor, representante)

        Returns:
            Lista de dicts com comissões calculadas (um por colaborador)
        """
        # Identificar colaboradores que recebem por recebimento neste processo
        colaboradores = self._get_payment_receivers_for_process(process_context)

        if not colaboradores:
            return []

        comissoes = []

        for colab in colaboradores:
            # Buscar regra de comissão
            regra = self.get_regra_comissao(
                process_context.get("linha"),
                process_context.get("grupo"),
                process_context.get("subgrupo"),
                process_context.get("tipo_mercadoria"),
                colab["cargo"],
            )

            if regra is None:
                continue

            # Extrair taxa e PE da regra
            try:
                taxa_rateio = float(regra.get("taxa_rateio_maximo_pct", 0)) / 100.0
                pe = float(regra.get("fatia_cargo_pct", 0)) / 100.0
            except (ValueError, TypeError):
                taxa_rateio = 0.0
                pe = 0.0

            # Calcular comissão: valor_recebido * taxa * PE (FC=1.0 para recebimentos)
            comissao = float(valor_recebido) * taxa_rateio * pe

            comissoes.append(
                {
                    "id_colaborador": colab.get("id_colaborador"),
                    "nome_colaborador": colab["nome"],
                    "cargo": colab["cargo"],
                    "processo": processo,
                    "linha": process_context.get("linha"),
                    "grupo": process_context.get("grupo"),
                    "subgrupo": process_context.get("subgrupo"),
                    "tipo_mercadoria": process_context.get("tipo_mercadoria"),
                    "faturamento_item": valor_recebido,
                    "taxa_rateio_aplicada": taxa_rateio,
                    "percentual_elegibilidade_pe": pe,
                    "fator_correcao_fc": 1.0,  # Sempre 1.0 para recebimentos
                    "comissao_calculada": comissao,
                    "tipo_lancamento": "Recebimento",
                    "observacao": "Comissao por Recebimento",
                }
            )

        return comissoes

    def _get_payment_receivers_for_process(self, process_context: Dict) -> List[Dict]:
        """
        Identifica colaboradores que recebem por recebimento no processo.

        Busca em dois grupos:
        1. Gestão: atribuições por contexto (linha, grupo, subgrupo, tipo)
        2. Operacional: consultor interno e representante do processo

        Args:
            process_context: Contexto do processo

        Returns:
            Lista de dicts com colaboradores: [{'nome': '...', 'cargo': '...', 'id_colaborador': ...}, ...]
        """
        colaboradores = []
        colaboradores_nomes = set()

        # 1. Buscar colaboradores de gestão por atribuições
        gestao_colabs = self._get_gestao_colaboradores(process_context)
        for colab in gestao_colabs:
            nome_norm = normalize_text(colab["nome"])
            if nome_norm in self.recebe_por_recebimento_norm:
                if nome_norm not in colaboradores_nomes:
                    colaboradores.append(colab)
                    colaboradores_nomes.add(nome_norm)

        # 2. Buscar colaboradores operacionais (consultor interno e representante)
        operacional_colabs = self._get_operacional_colaboradores(process_context)
        for colab in operacional_colabs:
            nome_norm = normalize_text(colab["nome"])
            if nome_norm in self.recebe_por_recebimento_norm:
                if nome_norm not in colaboradores_nomes:
                    colaboradores.append(colab)
                    colaboradores_nomes.add(nome_norm)

        return colaboradores

    def _get_gestao_colaboradores(self, process_context: Dict) -> List[Dict]:
        """
        Busca colaboradores de gestão por atribuições.

        Args:
            process_context: Contexto do processo

        Returns:
            Lista de colaboradores de gestão
        """
        if self.atribuicoes_df.empty or self.colaboradores_df.empty:
            return []

        # Filtrar atribuições por contexto
        try:
            # Identificar cargos de gestão
            cargos_gestao = self.colaboradores_df[
                self.colaboradores_df["tipo_cargo"] == "Gestão"
            ]["cargo"].unique()

            # Filtrar atribuições de gestão
            atribuicoes_gestao = self.atribuicoes_df[
                self.atribuicoes_df["cargo"].isin(cargos_gestao)
            ]

            if atribuicoes_gestao.empty:
                return []

            # Buscar atribuições que correspondem ao contexto
            mask = (
                (atribuicoes_gestao["linha"] == process_context.get("linha"))
                & (atribuicoes_gestao["grupo"] == process_context.get("grupo"))
                & (atribuicoes_gestao["subgrupo"] == process_context.get("subgrupo"))
                & (
                    atribuicoes_gestao["tipo_mercadoria"]
                    == process_context.get("tipo_mercadoria")
                )
            )

            atribuidos = atribuicoes_gestao[mask]

            if atribuidos.empty:
                return []

            # Buscar informações completas dos colaboradores
            colaboradores = []
            for _, atr in atribuidos.iterrows():
                nome_colab = atr.get("colaborador")
                cargo = atr.get("cargo")

                # Buscar id_colaborador
                colab_row = self.colaboradores_df[
                    self.colaboradores_df["nome_colaborador"] == nome_colab
                ]

                id_colab = (
                    colab_row.iloc[0]["id_colaborador"] if not colab_row.empty else None
                )

                colaboradores.append(
                    {"nome": nome_colab, "cargo": cargo, "id_colaborador": id_colab}
                )

            return colaboradores

        except Exception:
            return []

    def _get_operacional_colaboradores(self, process_context: Dict) -> List[Dict]:
        """
        Busca colaboradores operacionais (consultor interno e representante).

        Args:
            process_context: Contexto do processo

        Returns:
            Lista de colaboradores operacionais
        """
        if self.colaboradores_df.empty:
            return []

        nomes_operacionais = []

        # Consultor Interno
        consultor = process_context.get("consultor_interno")
        if consultor and pd.notna(consultor):
            nomes_operacionais.append(str(consultor).strip())

        # Representante
        representante = process_context.get("representante")
        if representante and pd.notna(representante):
            nomes_operacionais.append(str(representante).strip())

        if not nomes_operacionais:
            return []

        # Buscar informações dos colaboradores
        colaboradores = []
        for nome in nomes_operacionais:
            colab_row = self.colaboradores_df[
                self.colaboradores_df["nome_colaborador"] == nome
            ]

            if not colab_row.empty:
                colaboradores.append(
                    {
                        "nome": nome,
                        "cargo": colab_row.iloc[0]["cargo"],
                        "id_colaborador": colab_row.iloc[0]["id_colaborador"],
                    }
                )

        return colaboradores

    def is_payment_receiver(self, colaborador_nome: str) -> bool:
        """
        Verifica se um colaborador recebe por recebimento.

        Args:
            colaborador_nome: Nome do colaborador

        Returns:
            True se recebe por recebimento
        """
        return normalize_text(colaborador_nome) in self.recebe_por_recebimento_norm

    def get_payment_receivers_count(self) -> int:
        """
        Retorna quantidade de colaboradores que recebem por recebimento.

        Returns:
            Quantidade de colaboradores
        """
        return len(self.recebe_por_recebimento_ids)
