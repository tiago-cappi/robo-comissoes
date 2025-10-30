"""
Página para Adicionar e Remover Registros.
Permite adicionar novos registros e remover registros existentes das tabelas.
"""

import streamlit as st
import pandas as pd
from pathlib import Path
import sys
from datetime import datetime

# Adicionar o diretório frontend ao path
FRONTEND_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(FRONTEND_DIR))

from config.settings import REGRAS_COMISSOES_FILE, BACKUP_DIR
from utils.excel_handler import RegrasComissoesHandler
from components.backup_manager import BackupManager

# --- Configuração da Página ---
st.set_page_config(
    page_title="Adicionar/Remover",
    page_icon="➕",
    layout="wide",
)

# --- Título ---
st.title("➕ Adicionar e Remover Registros")
st.markdown(
    """
    Adicione novos registros ou remova registros existentes das tabelas.
    As alterações serão salvas automaticamente com backup.
"""
)

st.divider()


# --- Configuração das Abas Editáveis ---
# Definição das colunas exatas de cada aba do arquivo Regras_Comissoes.xlsx
SHEET_COLUMNS = {
    "CARGOS": ["nome_cargo", "tipo_cargo", "TIPO_COMISSAO"],
    "COLABORADORES": ["id_colaborador", "nome_colaborador", "cargo"],
    "HIERARQUIA": ["linha", "grupo", "subgrupo", "tipo_mercadoria", "fabricante"],
    "ATRIBUICOES": [
        "linha",
        "grupo",
        "subgrupo",
        "tipo_mercadoria",
        "colaborador",
        "cargo",
    ],
    "PESOS_METAS": [
        "cargo",
        "faturamento_linha",
        "rentabilidade",
        "conversao_linha",
        "faturamento_individual",
        "conversao_individual",
        "retencao_clientes",
        "meta_fornecedor_1",
        "meta_fornecedor_2",
        "Soma dos pesos",
    ],
    "METAS_INDIVIDUAIS": [
        "colaborador",
        "cargo",
        "tipo_meta",
        "valor_meta",
        "valor",
        "periodo",
    ],
    "METAS_APLICACAO": ["linha", "tipo_mercadoria", "tipo_meta", "valor_meta"],
    "CONFIG_COMISSAO": [
        "linha",
        "grupo",
        "subgrupo",
        "tipo_mercadoria",
        "cargo",
        "taxa_rateio_maximo_pct",
        "fatia_cargo_pct",
        "ativo",
    ],
    "ALIASES": ["entidade", "alias", "padrao"],
    "META_RENTABILIDADE": [
        "mes_ano",
        "tipo_meta",
        "linha",
        "grupo",
        "subgrupo",
        "tipo_mercadoria",
        "referencia_media_ponderada_pct",
        "meta_rentabilidade_alvo_pct",
    ],
    "METAS_FORNECEDORES": ["linha", "fabricante", "moeda", "meta_anual"],
    "CROSS_SELLING": ["colaborador", "taxa_cross_selling_pct"],
}

# Abas disponíveis para edição (ordenadas)
EDITABLE_SHEETS = [
    "CARGOS",
    "COLABORADORES",
    "HIERARQUIA",
    "ATRIBUICOES",
    "PESOS_METAS",
    "METAS_INDIVIDUAIS",
    "METAS_APLICACAO",
    "CONFIG_COMISSAO",
    "ALIASES",
    "META_RENTABILIDADE",
    "METAS_FORNECEDORES",
    "CROSS_SELLING",
]


# --- Funções Auxiliares ---
@st.cache_data(ttl=30)
def load_regras_data():
    """Carrega os dados do arquivo Regras_Comissoes.xlsx com cache."""
    handler = RegrasComissoesHandler(REGRAS_COMISSOES_FILE)

    if not handler.file_exists():
        st.error(f"❌ Arquivo não encontrado: {REGRAS_COMISSOES_FILE}")
        return None, None

    # Ler todas as abas editáveis
    sheets = {}
    for sheet_name in EDITABLE_SHEETS:
        try:
            df = handler.read_sheet(sheet_name)
            sheets[sheet_name] = df
        except Exception as e:
            st.warning(f"⚠️ Erro ao ler aba {sheet_name}: {e}")

    return handler, sheets


def generate_next_id(df: pd.DataFrame, id_column: str, prefix: str = "C") -> str:
    """
    Gera o próximo ID disponível para uma tabela.

    Args:
        df: DataFrame
        id_column: Nome da coluna de ID
        prefix: Prefixo do ID (ex: 'C' para C001)

    Returns:
        Próximo ID disponível
    """
    if df.empty or id_column not in df.columns:
        return f"{prefix}001"

    # Extrair números dos IDs existentes
    existing_ids = df[id_column].dropna().astype(str).tolist()

    # Filtrar IDs com o prefixo correto
    numbers = []
    for id_val in existing_ids:
        if id_val.startswith(prefix):
            try:
                num = int(id_val[len(prefix) :])
                numbers.append(num)
            except ValueError:
                continue

    if not numbers:
        return f"{prefix}001"

    # Próximo número
    next_num = max(numbers) + 1
    return f"{prefix}{next_num:03d}"


def get_field_type(column_name: str, sheet_name: str) -> dict:
    """
    Retorna o tipo de campo apropriado para uma coluna.

    Args:
        column_name: Nome da coluna
        sheet_name: Nome da aba

    Returns:
        Dicionário com configuração do campo
    """
    # Campos percentuais
    if any(
        term in column_name.lower()
        for term in ["pct", "taxa", "fatia", "referencia", "meta_rentabilidade"]
    ):
        return {
            "type": "number",
            "min_value": 0.0,
            "max_value": 100.0,
            "step": 0.1,
            "format": "%.2f",
            "help": "Valor percentual (0-100%)",
        }

    # Campos monetários/valores
    if any(
        term in column_name.lower()
        for term in ["valor", "meta_anual", "faturamento", "rentabilidade"]
    ):
        return {
            "type": "number",
            "min_value": 0.0,
            "step": 100.0,
            "format": "%.2f",
            "help": "Valor numérico",
        }

    # Campos de ID
    if "id_" in column_name.lower():
        return {
            "type": "text",
            "help": "ID será gerado automaticamente",
            "disabled": True,
        }

    # Campos específicos conhecidos com opções
    field_options = {
        "cargo": [
            "Diretor",
            "Gerente Geral",
            "Gerente Linha",
            "Coordenador",
            "Vendedor",
            "Analista",
        ],
        "tipo_cargo": ["Vendas", "Gerência", "Diretoria", "Suporte"],
        "TIPO_COMISSAO": ["Percentual", "Fixa", "Mista", "Sem comissão"],
        "entidade": ["colaborador", "cliente", "fornecedor", "produto"],
        "tipo_meta": ["Faturamento", "Rentabilidade", "Conversão", "Retenção"],
        "periodo": ["Mensal", "Trimestral", "Anual"],
        "moeda": ["BRL", "USD", "EUR"],
        "ativo": ["Sim", "Não"],
        "mes_ano": [f"{m:02d}/2025" for m in range(1, 13)],
    }

    if column_name in field_options:
        return {"type": "select", "options": field_options[column_name]}

    # Campo de soma (desabilitado)
    if "soma" in column_name.lower():
        return {"type": "number", "help": "Calculado automaticamente", "disabled": True}

    # Padrão: campo de texto
    return {"type": "text", "help": f"Digite o valor para {column_name}"}


def render_dynamic_form(sheet_name: str, columns: list) -> dict:
    """
    Renderiza um formulário dinâmico baseado nas colunas da aba.

    Args:
        sheet_name: Nome da aba
        columns: Lista de colunas

    Returns:
        Dicionário com valores ou None
    """
    st.subheader(f"➕ Adicionar Registro em {sheet_name}")

    # Carregar dados para gerar IDs e obter opções
    handler, sheets = load_regras_data()
    if handler is None or sheets is None:
        return None

    df_current = sheets.get(sheet_name, pd.DataFrame())

    with st.form(f"add_{sheet_name}_form", clear_on_submit=True):
        new_record = {}

        # Dividir campos em colunas para melhor layout
        num_fields = len(columns)
        cols_per_row = 2
        num_rows = (num_fields + cols_per_row - 1) // cols_per_row

        field_index = 0
        for row in range(num_rows):
            cols = st.columns(cols_per_row)

            for col_idx in range(cols_per_row):
                if field_index >= num_fields:
                    break

                column_name = columns[field_index]
                field_config = get_field_type(column_name, sheet_name)

                with cols[col_idx]:
                    # ID automático
                    if "id_" in column_name.lower():
                        next_id = generate_next_id(df_current, column_name, prefix="C")
                        st.info(f"💡 {column_name}: {next_id} (automático)")
                        new_record[column_name] = next_id

                    # Campo desabilitado
                    elif field_config.get("disabled", False):
                        st.text_input(
                            column_name,
                            value="",
                            disabled=True,
                            help=field_config.get("help", ""),
                        )
                        new_record[column_name] = None

                    # Select
                    elif field_config["type"] == "select":
                        value = st.selectbox(
                            f"{column_name} *",
                            options=field_config.get("options", []),
                            help=field_config.get("help", ""),
                        )
                        new_record[column_name] = value

                    # Número
                    elif field_config["type"] == "number":
                        value = st.number_input(
                            f"{column_name} *",
                            min_value=field_config.get("min_value", 0.0),
                            max_value=field_config.get("max_value", 1000000.0),
                            step=field_config.get("step", 1.0),
                            format=field_config.get("format", "%.2f"),
                            help=field_config.get("help", ""),
                        )
                        new_record[column_name] = value

                    # Texto
                    else:
                        value = st.text_input(
                            f"{column_name} *",
                            help=field_config.get("help", ""),
                            placeholder=f"Digite {column_name}",
                        )
                        new_record[column_name] = value

                field_index += 1

        st.markdown("---")

        submitted = st.form_submit_button(
            f"➕ Adicionar em {sheet_name}", type="primary"
        )

        if submitted:
            # Validar campos obrigatórios (não vazios e não None)
            empty_fields = [
                col
                for col in columns
                if "id_" not in col.lower()
                and "soma" not in col.lower()
                and (new_record.get(col) == "" or new_record.get(col) is None)
            ]

            if empty_fields:
                st.error(f"❌ Campos obrigatórios vazios: {', '.join(empty_fields)}")
                return None

            return new_record

    return None


def render_remove_records(df: pd.DataFrame, sheet_name: str, id_column: str = None):
    """
    Renderiza interface para remover registros.

    Args:
        df: DataFrame com os registros
        sheet_name: Nome da aba
        id_column: Coluna de ID (opcional)
    """
    st.subheader(f"🗑️ Remover Registros de {sheet_name}")

    if df.empty:
        st.info("Não há registros para remover.")
        return None

    # Mostrar tabela com seleção
    st.markdown("**Selecione os registros para remover:**")

    # Adicionar coluna de seleção
    df_display = df.copy()
    df_display.insert(0, "Selecionar", False)

    # Editor para seleção
    edited_df = st.data_editor(
        df_display,
        use_container_width=True,
        num_rows="fixed",
        column_config={
            "Selecionar": st.column_config.CheckboxColumn(
                "Selecionar", help="Marque para remover", default=False
            )
        },
        disabled=[col for col in df_display.columns if col != "Selecionar"],
        key=f"remove_{sheet_name}",
        height=400,
    )

    # Contar selecionados
    selected_count = edited_df["Selecionar"].sum()

    if selected_count > 0:
        st.warning(f"⚠️ {selected_count} registro(s) selecionado(s) para remoção")

        col_remove, col_cancel = st.columns(2)

        with col_remove:
            if st.button(
                f"🗑️ Remover {selected_count} Registro(s)",
                type="primary",
                use_container_width=True,
            ):
                # Confirmar remoção
                if st.session_state.get("confirm_remove", False):
                    # Filtrar registros não selecionados
                    df_filtered = df[~edited_df["Selecionar"]].reset_index(drop=True)
                    return df_filtered
                else:
                    st.session_state["confirm_remove"] = True
                    st.warning(
                        "⚠️ Clique novamente para confirmar a remoção dos registros."
                    )
                    st.rerun()

        with col_cancel:
            if st.button("❌ Cancelar", use_container_width=True):
                if "confirm_remove" in st.session_state:
                    del st.session_state["confirm_remove"]
                st.rerun()

    return None


# --- Carregar Dados ---
with st.spinner("Carregando dados..."):
    handler, all_sheets = load_regras_data()

if handler is None or all_sheets is None:
    st.error("❌ Erro ao carregar dados.")
    st.stop()

# --- Exibir Status ---
st.success(f"✅ Arquivo carregado: `{REGRAS_COMISSOES_FILE.name}`")
st.divider()

# --- Modo: Adicionar ou Remover ---
st.header("📋 Selecione a Operação")

operation = st.radio(
    "O que deseja fazer?",
    options=["➕ Adicionar Registros", "🗑️ Remover Registros"],
    horizontal=True,
)

st.divider()

# --- ADICIONAR REGISTROS ---
if operation == "➕ Adicionar Registros":
    st.header("➕ Adicionar Novo Registro")

    # Seleção de aba
    sheet_icons = {
        "CARGOS": "💼",
        "COLABORADORES": "👥",
        "HIERARQUIA": "🏢",
        "ATRIBUICOES": "📋",
        "PESOS_METAS": "⚖️",
        "METAS_INDIVIDUAIS": "🎯",
        "METAS_APLICACAO": "📊",
        "CONFIG_COMISSAO": "💰",
        "ALIASES": "🔄",
        "META_RENTABILIDADE": "💹",
        "METAS_FORNECEDORES": "🏭",
        "CROSS_SELLING": "🤝",
    }

    selected_sheet = st.selectbox(
        "Selecione a tabela:",
        options=EDITABLE_SHEETS,
        format_func=lambda x: f"{sheet_icons.get(x, '📄')} {x}",
    )

    st.markdown("---")

    # Obter colunas da aba selecionada
    columns = SHEET_COLUMNS.get(selected_sheet, [])

    if not columns:
        st.error(f"❌ Configuração de colunas não encontrada para {selected_sheet}")
        new_record = None
    else:
        # Renderizar formulário dinâmico
        new_record = render_dynamic_form(selected_sheet, columns)

    # Se um novo registro foi criado, salvar
    if new_record is not None:
        with st.spinner("Adicionando registro..."):
            try:
                # Carregar dados atuais
                df_current = all_sheets[selected_sheet]

                # Adicionar novo registro
                df_updated = pd.concat(
                    [df_current, pd.DataFrame([new_record])], ignore_index=True
                )

                # Criar backup
                backup_manager = BackupManager(BACKUP_DIR)
                backup_path = backup_manager.create_backup(REGRAS_COMISSOES_FILE)

                if backup_path:
                    st.success(f"✅ Backup criado: `{backup_path.name}`")

                # Salvar alterações
                success = handler.write_sheet(df_updated, selected_sheet, mode="update")

                if success:
                    st.success("✅ Registro adicionado com sucesso!")
                    st.balloons()

                    # Limpar cache
                    st.cache_data.clear()

                    # Aguardar um pouco
                    import time

                    time.sleep(2)

                    # Recarregar
                    st.rerun()
                else:
                    st.error("❌ Erro ao salvar registro.")

            except Exception as e:
                st.error(f"❌ Erro ao adicionar registro: {e}")

# --- REMOVER REGISTROS ---
else:
    st.header("🗑️ Remover Registros Existentes")

    # Seleção de aba
    sheet_icons = {
        "CARGOS": "💼",
        "COLABORADORES": "👥",
        "HIERARQUIA": "🏢",
        "ATRIBUICOES": "📋",
        "PESOS_METAS": "⚖️",
        "METAS_INDIVIDUAIS": "🎯",
        "METAS_APLICACAO": "📊",
        "CONFIG_COMISSAO": "💰",
        "ALIASES": "🔄",
        "META_RENTABILIDADE": "💹",
        "METAS_FORNECEDORES": "🏭",
        "CROSS_SELLING": "🤝",
    }

    selected_sheet = st.selectbox(
        "Selecione a tabela:",
        options=EDITABLE_SHEETS,
        format_func=lambda x: f"{sheet_icons.get(x, '📄')} {x}",
    )

    st.markdown("---")

    # Renderizar interface de remoção
    df_current = all_sheets[selected_sheet]

    # Determinar coluna de ID (se houver)
    id_column = None
    if "id_colaborador" in df_current.columns:
        id_column = "id_colaborador"
    elif "id" in df_current.columns:
        id_column = "id"

    df_filtered = render_remove_records(df_current, selected_sheet, id_column)

    # Se registros foram removidos, salvar
    if df_filtered is not None:
        with st.spinner("Removendo registros..."):
            try:
                # Criar backup
                backup_manager = BackupManager(BACKUP_DIR)
                backup_path = backup_manager.create_backup(REGRAS_COMISSOES_FILE)

                if backup_path:
                    st.success(f"✅ Backup criado: `{backup_path.name}`")

                # Salvar alterações
                success = handler.write_sheet(
                    df_filtered, selected_sheet, mode="update"
                )

                if success:
                    removed_count = len(df_current) - len(df_filtered)
                    st.success(
                        f"✅ {removed_count} registro(s) removido(s) com sucesso!"
                    )

                    # Limpar estado de confirmação
                    if "confirm_remove" in st.session_state:
                        del st.session_state["confirm_remove"]

                    # Limpar cache
                    st.cache_data.clear()

                    # Aguardar um pouco
                    import time

                    time.sleep(2)

                    # Recarregar
                    st.rerun()
                else:
                    st.error("❌ Erro ao salvar alterações.")

            except Exception as e:
                st.error(f"❌ Erro ao remover registros: {e}")

# --- Informações de Ajuda ---
st.divider()

with st.expander("ℹ️ Como Usar Esta Página", expanded=False):
    st.markdown(
        """
        ### ➕ Adicionar Registros
        
        1. **Selecione "Adicionar Registros"**
        2. **Escolha a tabela** onde deseja adicionar
        3. **Preencha o formulário** com os dados do novo registro
        4. **Clique em "Adicionar"** para salvar
        
        **Importante:**
        - IDs são gerados automaticamente quando aplicável
        - Campos marcados com * são obrigatórios
        - Um backup é criado antes de cada adição
        
        ### 🗑️ Remover Registros
        
        1. **Selecione "Remover Registros"**
        2. **Escolha a tabela** onde deseja remover
        3. **Marque os registros** na coluna "Selecionar"
        4. **Clique em "Remover"** (você precisará confirmar)
        
        **Importante:**
        - Você precisa confirmar clicando duas vezes para remover
        - Um backup é criado antes de cada remoção
        - A remoção é permanente (mas pode ser restaurada via backup)
        
        ### 💾 Backups
        
        - Backup automático antes de cada operação
        - Backups salvos em `frontend/backups/`
        - Podem ser restaurados na página de Edição
        
        ### ⚠️ Atenção
        
        - Sempre revise os dados antes de adicionar/remover
        - Operações são salvas imediatamente
        - Use os backups para desfazer alterações se necessário
    """
    )

# --- Botões de Ação Rápida ---
st.divider()
col_refresh, col_stats = st.columns(2)

with col_refresh:
    if st.button("🔄 Recarregar Dados", use_container_width=True):
        if "confirm_remove" in st.session_state:
            del st.session_state["confirm_remove"]
        st.cache_data.clear()
        st.rerun()

with col_stats:
    # Estatísticas rápidas - total de registros em todas as abas
    total_registros = sum(len(df) for df in all_sheets.values() if not df.empty)
    total_abas = len([df for df in all_sheets.values() if not df.empty])

    st.metric(
        "📊 Total de Registros",
        f"{total_registros}",
        help=f"Distribuído em {total_abas} abas editáveis",
    )
