"""
Módulo para manipulação de arquivos Excel.
Funções para ler e escrever dados do arquivo Regras_Comissoes.xlsx
e outros arquivos Excel usados pelo robô de comissões.
"""

import pandas as pd
import openpyxl
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import streamlit as st


class ExcelHandler:
    """Classe para manipular arquivos Excel do robô de comissões."""

    def __init__(self, file_path: Path):
        """
        Inicializa o handler com o caminho do arquivo Excel.

        Args:
            file_path: Caminho para o arquivo Excel
        """
        self.file_path = Path(file_path)
        self._workbook = None
        self._sheets_data = {}

    def file_exists(self) -> bool:
        """Verifica se o arquivo existe."""
        return self.file_path.exists()

    def get_sheet_names(self) -> List[str]:
        """
        Retorna a lista de nomes das abas do arquivo Excel.

        Returns:
            Lista com os nomes das abas
        """
        try:
            wb = openpyxl.load_workbook(self.file_path, read_only=True)
            sheet_names = wb.sheetnames
            wb.close()
            return sheet_names
        except Exception as e:
            st.error(f"Erro ao ler nomes das abas: {e}")
            return []

    def read_sheet(self, sheet_name: str, **kwargs) -> pd.DataFrame:
        """
        Lê uma aba específica do arquivo Excel.

        Args:
            sheet_name: Nome da aba a ser lida
            **kwargs: Argumentos adicionais para pd.read_excel

        Returns:
            DataFrame com os dados da aba
        """
        try:
            df = pd.read_excel(self.file_path, sheet_name=sheet_name, **kwargs)
            self._sheets_data[sheet_name] = df
            return df
        except Exception as e:
            st.error(f"Erro ao ler aba '{sheet_name}': {e}")
            return pd.DataFrame()

    def read_all_sheets(self) -> Dict[str, pd.DataFrame]:
        """
        Lê todas as abas do arquivo Excel.

        Returns:
            Dicionário com nome_aba: DataFrame
        """
        try:
            all_sheets = pd.read_excel(self.file_path, sheet_name=None)
            self._sheets_data = all_sheets
            return all_sheets
        except Exception as e:
            st.error(f"Erro ao ler todas as abas: {e}")
            return {}

    def write_sheet(
        self, df: pd.DataFrame, sheet_name: str, mode: str = "replace"
    ) -> bool:
        """
        Escreve um DataFrame em uma aba do arquivo Excel.

        Args:
            df: DataFrame a ser escrito
            sheet_name: Nome da aba
            mode: 'replace' para substituir o arquivo, 'update' para atualizar uma aba

        Returns:
            True se sucesso, False caso contrário
        """
        try:
            if mode == "replace":
                # Substituir o arquivo inteiro
                with pd.ExcelWriter(self.file_path, engine="openpyxl") as writer:
                    df.to_excel(writer, sheet_name=sheet_name, index=False)
                return True

            elif mode == "update":
                # Atualizar apenas uma aba (preservar outras)
                if not self.file_exists():
                    # Se não existe, criar novo
                    with pd.ExcelWriter(self.file_path, engine="openpyxl") as writer:
                        df.to_excel(writer, sheet_name=sheet_name, index=False)
                    return True

                # Carregar workbook existente
                with pd.ExcelWriter(
                    self.file_path,
                    engine="openpyxl",
                    mode="a",
                    if_sheet_exists="replace",
                ) as writer:
                    df.to_excel(writer, sheet_name=sheet_name, index=False)
                return True

            else:
                st.error(f"Modo '{mode}' inválido. Use 'replace' ou 'update'.")
                return False

        except Exception as e:
            st.error(f"Erro ao escrever aba '{sheet_name}': {e}")
            return False

    def write_multiple_sheets(self, sheets_dict: Dict[str, pd.DataFrame]) -> bool:
        """
        Escreve múltiplas abas no arquivo Excel.

        Args:
            sheets_dict: Dicionário com nome_aba: DataFrame

        Returns:
            True se sucesso, False caso contrário
        """
        try:
            with pd.ExcelWriter(self.file_path, engine="openpyxl") as writer:
                for sheet_name, df in sheets_dict.items():
                    df.to_excel(writer, sheet_name=sheet_name, index=False)
            return True
        except Exception as e:
            st.error(f"Erro ao escrever múltiplas abas: {e}")
            return False

    def get_cached_sheet(self, sheet_name: str) -> Optional[pd.DataFrame]:
        """
        Retorna uma aba já lida (cache).

        Args:
            sheet_name: Nome da aba

        Returns:
            DataFrame se já foi lido, None caso contrário
        """
        return self._sheets_data.get(sheet_name)

    def clear_cache(self):
        """Limpa o cache de abas lidas."""
        self._sheets_data = {}


class RegrasComissoesHandler(ExcelHandler):
    """Handler específico para o arquivo Regras_Comissoes.xlsx."""

    # Nomes esperados das abas (baseado na estrutura real do arquivo)
    EXPECTED_SHEETS = [
        "README",
        "PARAMS",
        "CARGOS",
        "COLABORADORES",
        "HIERARQUIA",
        "ATRIBUICOES",
        "PESOS_METAS",
        "METAS_INDIVIDUAIS",
        "METAS_APLICACAO",
        "CONFIG_COMISSAO",
        "ENUM_TIPO_META",
        "ALIASES",
        "DICIONARIO",
        "META_RENTABILIDADE",
        "METAS_FORNECEDORES",
        "CROSS_SELLING",
    ]

    # Abas principais que serão editadas no frontend
    CORE_SHEETS = [
        "COLABORADORES",
        "ALIASES",
        "CARGOS",
        "METAS_INDIVIDUAIS",
        "CONFIG_COMISSAO",
    ]

    def validate_structure(self) -> Tuple[bool, List[str]]:
        """
        Valida se o arquivo tem a estrutura esperada.

        Returns:
            (is_valid, missing_sheets)
        """
        if not self.file_exists():
            return False, ["Arquivo não encontrado"]

        existing_sheets = self.get_sheet_names()
        missing_sheets = [
            sheet for sheet in self.EXPECTED_SHEETS if sheet not in existing_sheets
        ]

        return len(missing_sheets) == 0, missing_sheets

    def read_colaboradores(self) -> pd.DataFrame:
        """Lê a aba COLABORADORES."""
        return self.read_sheet("COLABORADORES")

    def read_aliases(self) -> pd.DataFrame:
        """Lê a aba ALIASES."""
        return self.read_sheet("ALIASES")

    def read_estrutura(self) -> pd.DataFrame:
        """Lê a aba ESTRUTURA."""
        return self.read_sheet("ESTRUTURA")

    def read_metas(self) -> pd.DataFrame:
        """Lê a aba METAS."""
        return self.read_sheet("METAS")

    def read_comissoes(self) -> pd.DataFrame:
        """Lê a aba COMISSOES."""
        return self.read_sheet("COMISSOES")

    def write_colaboradores(self, df: pd.DataFrame) -> bool:
        """Atualiza a aba COLABORADORES."""
        return self.write_sheet(df, "COLABORADORES", mode="update")

    def write_aliases(self, df: pd.DataFrame) -> bool:
        """Atualiza a aba ALIASES."""
        return self.write_sheet(df, "ALIASES", mode="update")

    def write_estrutura(self, df: pd.DataFrame) -> bool:
        """Atualiza a aba ESTRUTURA."""
        return self.write_sheet(df, "ESTRUTURA", mode="update")

    def write_metas(self, df: pd.DataFrame) -> bool:
        """Atualiza a aba METAS."""
        return self.write_sheet(df, "METAS", mode="update")

    def write_comissoes(self, df: pd.DataFrame) -> bool:
        """Atualiza a aba COMISSOES."""
        return self.write_sheet(df, "COMISSOES", mode="update")


def load_regras_comissoes(file_path: Path) -> Optional[RegrasComissoesHandler]:
    """
    Carrega o arquivo Regras_Comissoes.xlsx e valida sua estrutura.

    Args:
        file_path: Caminho para o arquivo

    Returns:
        RegrasComissoesHandler se válido, None caso contrário
    """
    handler = RegrasComissoesHandler(file_path)

    if not handler.file_exists():
        st.error(f"Arquivo nao encontrado: {file_path}")
        return None

    is_valid, missing_sheets = handler.validate_structure()

    if not is_valid:
        st.warning(
            f"Aviso: Algumas abas nao foram encontradas: {', '.join(missing_sheets)}"
        )
        # Retorna mesmo assim para permitir trabalhar com abas parciais

    return handler
