"""
Módulo para validação de dados.
Valida a estrutura e conteúdo dos arquivos Excel e CSV
usados pelo robô de comissões.
"""

import pandas as pd
from typing import Dict, List, Tuple, Optional
import streamlit as st


class DataValidator:
    """Classe base para validação de dados."""

    @staticmethod
    def validate_required_columns(
        df: pd.DataFrame, required_columns: List[str], sheet_name: str = "DataFrame"
    ) -> Tuple[bool, List[str]]:
        """
        Valida se todas as colunas obrigatórias estão presentes.

        Args:
            df: DataFrame a ser validado
            required_columns: Lista de colunas obrigatórias
            sheet_name: Nome da aba/arquivo (para mensagens de erro)

        Returns:
            (is_valid, missing_columns)
        """
        if df.empty:
            return False, required_columns

        existing_columns = df.columns.tolist()
        missing_columns = [
            col for col in required_columns if col not in existing_columns
        ]

        if missing_columns:
            st.warning(
                f"⚠️ Aba '{sheet_name}': "
                f"Colunas faltando: {', '.join(missing_columns)}"
            )

        return len(missing_columns) == 0, missing_columns

    @staticmethod
    def validate_no_empty_values(
        df: pd.DataFrame, columns: List[str], sheet_name: str = "DataFrame"
    ) -> Tuple[bool, Dict[str, int]]:
        """
        Valida se as colunas especificadas não têm valores vazios.

        Args:
            df: DataFrame a ser validado
            columns: Lista de colunas a verificar
            sheet_name: Nome da aba/arquivo

        Returns:
            (is_valid, empty_counts_per_column)
        """
        empty_counts = {}

        for col in columns:
            if col in df.columns:
                empty_count = df[col].isna().sum()
                if empty_count > 0:
                    empty_counts[col] = empty_count

        if empty_counts:
            st.warning(
                f"⚠️ Aba '{sheet_name}': " f"Valores vazios encontrados: {empty_counts}"
            )

        return len(empty_counts) == 0, empty_counts

    @staticmethod
    def validate_numeric_columns(
        df: pd.DataFrame, columns: List[str], sheet_name: str = "DataFrame"
    ) -> Tuple[bool, List[str]]:
        """
        Valida se as colunas especificadas contêm valores numéricos.

        Args:
            df: DataFrame a ser validado
            columns: Lista de colunas que devem ser numéricas
            sheet_name: Nome da aba/arquivo

        Returns:
            (is_valid, non_numeric_columns)
        """
        non_numeric = []

        for col in columns:
            if col in df.columns:
                if not pd.api.types.is_numeric_dtype(df[col]):
                    # Tentar converter
                    try:
                        pd.to_numeric(df[col], errors="raise")
                    except (ValueError, TypeError):
                        non_numeric.append(col)

        if non_numeric:
            st.warning(
                f"⚠️ Aba '{sheet_name}': "
                f"Colunas não-numéricas: {', '.join(non_numeric)}"
            )

        return len(non_numeric) == 0, non_numeric


class RegrasComissoesValidator(DataValidator):
    """Validador específico para o arquivo Regras_Comissoes.xlsx."""

    # Estrutura esperada de cada aba
    # Baseado na estrutura real do arquivo Regras_Comissoes.xlsx do backend
    SCHEMA = {
        "COLABORADORES": {
            "required_columns": ["id_colaborador", "nome_colaborador", "cargo"],
            "non_empty_columns": ["nome_colaborador", "cargo"],
            "numeric_columns": [],
        },
        "ALIASES": {
            "required_columns": ["entidade", "alias", "padrao"],
            "non_empty_columns": [
                "entidade",
                "padrao",
            ],  # alias pode ser vazio em algumas linhas
            "numeric_columns": [],
        },
        "ESTRUTURA": {
            "required_columns": ["cargo", "tipo_comissao", "prioridade"],
            "non_empty_columns": ["cargo", "tipo_comissao"],
            "numeric_columns": ["prioridade"],
        },
        "METAS": {
            "required_columns": [
                "cargo",
                "colaborador",
                "mes",
                "ano",
                "tipo_meta",
                "valor",
                "peso",
            ],
            "non_empty_columns": ["cargo", "mes", "ano", "tipo_meta"],
            "numeric_columns": ["mes", "ano", "valor", "peso"],
        },
        "COMISSOES": {
            "required_columns": ["cargo", "regra", "percentual_base", "tipo_calculo"],
            "non_empty_columns": ["cargo", "regra", "tipo_calculo"],
            "numeric_columns": ["percentual_base"],
        },
    }

    @classmethod
    def validate_sheet(
        cls, df: pd.DataFrame, sheet_name: str
    ) -> Tuple[bool, List[str]]:
        """
        Valida uma aba específica do arquivo Regras_Comissoes.xlsx.

        Args:
            df: DataFrame da aba
            sheet_name: Nome da aba

        Returns:
            (is_valid, error_messages)
        """
        errors = []

        if sheet_name not in cls.SCHEMA:
            errors.append(f"Aba '{sheet_name}' não reconhecida")
            return False, errors

        schema = cls.SCHEMA[sheet_name]

        # Validar colunas obrigatórias
        is_valid, missing = cls.validate_required_columns(
            df, schema["required_columns"], sheet_name
        )
        if not is_valid:
            errors.append(f"Colunas faltando: {', '.join(missing)}")

        # Validar valores não-vazios
        is_valid, empty = cls.validate_no_empty_values(
            df, schema["non_empty_columns"], sheet_name
        )
        if not is_valid:
            errors.append(f"Valores vazios em: {', '.join(empty.keys())}")

        # Validar colunas numéricas
        is_valid, non_numeric = cls.validate_numeric_columns(
            df, schema["numeric_columns"], sheet_name
        )
        if not is_valid:
            errors.append(f"Colunas não-numéricas: {', '.join(non_numeric)}")

        return len(errors) == 0, errors

    @classmethod
    def validate_all_sheets(
        cls, sheets_dict: Dict[str, pd.DataFrame]
    ) -> Tuple[bool, Dict[str, List[str]]]:
        """
        Valida todas as abas do arquivo Regras_Comissoes.xlsx.

        Args:
            sheets_dict: Dicionário com nome_aba: DataFrame

        Returns:
            (is_valid, errors_per_sheet)
        """
        all_errors = {}

        for sheet_name, df in sheets_dict.items():
            is_valid, errors = cls.validate_sheet(df, sheet_name)
            if not is_valid:
                all_errors[sheet_name] = errors

        return len(all_errors) == 0, all_errors


class InputFilesValidator(DataValidator):
    """Validador para os arquivos de entrada (Analise_Comercial_Completa, etc.)."""

    @staticmethod
    def validate_analise_comercial(df: pd.DataFrame) -> Tuple[bool, List[str]]:
        """
        Valida o arquivo Analise_Comercial_Completa.

        Args:
            df: DataFrame do arquivo

        Returns:
            (is_valid, error_messages)
        """
        errors = []

        required_columns = [
            "Processo",
            "Cliente",
            "Consultor Interno",
            "Status Processo",
            "Data Pedido",
        ]

        is_valid, missing = DataValidator.validate_required_columns(
            df, required_columns, "Analise_Comercial_Completa"
        )

        if not is_valid:
            errors.append(f"Colunas faltando: {', '.join(missing)}")

        return len(errors) == 0, errors

    @staticmethod
    def validate_fin_conci(df: pd.DataFrame) -> Tuple[bool, List[str]]:
        """
        Valida o arquivo fin_conci_adcli_m3.xls.

        Args:
            df: DataFrame do arquivo

        Returns:
            (is_valid, error_messages)
        """
        errors = []

        # O arquivo tem estrutura variável, validação básica
        if df.empty:
            errors.append("Arquivo vazio")

        return len(errors) == 0, errors

    @staticmethod
    def validate_fin_adcli(df: pd.DataFrame) -> Tuple[bool, List[str]]:
        """
        Valida o arquivo fin_adcli_pg_m3.xls.

        Args:
            df: DataFrame do arquivo

        Returns:
            (is_valid, error_messages)
        """
        errors = []

        # O arquivo tem estrutura variável, validação básica
        if df.empty:
            errors.append("Arquivo vazio")

        return len(errors) == 0, errors
