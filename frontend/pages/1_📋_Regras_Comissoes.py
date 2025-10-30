"""
Página de Visualização e Edição das Regras de Comissões.
Permite visualizar e editar as informações do arquivo Regras_Comissoes.xlsx.
"""

import streamlit as st
import pandas as pd
from pathlib import Path
import sys

# Adicionar o diretório frontend ao path
FRONTEND_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(FRONTEND_DIR))

from config.settings import REGRAS_COMISSOES_FILE
from utils.excel_handler import RegrasComissoesHandler
from utils.data_validator import RegrasComissoesValidator


# --- Configuração da Página ---
st.set_page_config(
    page_title="Regras de Comissões",
    page_icon="📋",
    layout="wide",
)

# --- Título ---
st.title("📋 Regras de Comissões")
st.markdown(
    """
    Visualize e edite as regras de comissões do seu sistema.
    As alterações serão salvas no arquivo `Regras_Comissoes.xlsx`.
"""
)

st.divider()


# --- Funções Auxiliares ---
@st.cache_data(ttl=60)
def load_regras_data():
    """Carrega os dados do arquivo Regras_Comissoes.xlsx com cache."""
    handler = RegrasComissoesHandler(REGRAS_COMISSOES_FILE)

    if not handler.file_exists():
        st.error(f"❌ Arquivo não encontrado: {REGRAS_COMISSOES_FILE}")
        return None, None

    # Ler todas as abas
    all_sheets = handler.read_all_sheets()

    if not all_sheets:
        st.error("❌ Erro ao ler o arquivo Excel.")
        return None, None

    return handler, all_sheets


def display_dataframe_info(df: pd.DataFrame, sheet_name: str):
    """Exibe informações sobre o DataFrame."""
    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("📊 Total de Linhas", len(df))

    with col2:
        st.metric("📝 Total de Colunas", len(df.columns))

    with col3:
        # Contar valores vazios
        empty_count = df.isna().sum().sum()
        st.metric("⚠️ Células Vazias", empty_count)


def render_sheet_view(df: pd.DataFrame, sheet_name: str):
    """Renderiza a visualização de uma aba."""

    if df.empty:
        st.warning(f"⚠️ A aba '{sheet_name}' está vazia.")
        return

    # Mostrar informações
    display_dataframe_info(df, sheet_name)

    st.markdown("---")

    # Opções de visualização
    col1, col2 = st.columns([3, 1])

    with col1:
        st.subheader(f"📄 Dados da aba: {sheet_name}")

    with col2:
        # Opção para mostrar/ocultar colunas
        show_all_cols = st.checkbox(
            "Mostrar todas as colunas", value=True, key=f"show_all_{sheet_name}"
        )

    # Exibir o DataFrame
    if show_all_cols:
        st.dataframe(
            df,
            use_container_width=True,
            height=400,
        )
    else:
        # Permitir selecionar colunas
        selected_cols = st.multiselect(
            "Selecione as colunas para exibir:",
            options=df.columns.tolist(),
            default=df.columns.tolist()[:5],  # Primeiras 5 por padrão
            key=f"cols_{sheet_name}",
        )

        if selected_cols:
            st.dataframe(
                df[selected_cols],
                use_container_width=True,
                height=400,
            )
        else:
            st.info("Selecione pelo menos uma coluna para visualizar.")

    # Botão para baixar CSV
    st.download_button(
        label=f"📥 Baixar {sheet_name} como CSV",
        data=df.to_csv(index=False).encode("utf-8"),
        file_name=f"{sheet_name}.csv",
        mime="text/csv",
        key=f"download_{sheet_name}",
    )


# --- Carregar Dados ---
with st.spinner("Carregando dados..."):
    handler, all_sheets = load_regras_data()

if handler is None or all_sheets is None:
    st.stop()

# --- Exibir Status do Arquivo ---
st.success(f"✅ Arquivo carregado com sucesso: `{REGRAS_COMISSOES_FILE.name}`")

# Validar estrutura
is_valid, missing = handler.validate_structure()
if not is_valid:
    st.warning(f"⚠️ Algumas abas esperadas não foram encontradas: {', '.join(missing)}")

st.divider()

# --- Abas Principais ---
st.header("📌 Abas Principais")
st.markdown("Edite as informações mais importantes das regras de comissões:")

# Criar tabs para as abas principais
core_tabs = st.tabs(
    [
        "👥 COLABORADORES",
        "🔄 ALIASES",
        "💼 CARGOS",
        "🎯 METAS INDIVIDUAIS",
        "💰 CONFIG COMISSÃO",
    ]
)

# Tab 1: COLABORADORES
with core_tabs[0]:
    if "COLABORADORES" in all_sheets:
        df_colab = all_sheets["COLABORADORES"]
        render_sheet_view(df_colab, "COLABORADORES")

        # Informação adicional
        with st.expander("ℹ️ Sobre esta aba"):
            st.markdown(
                """
                **COLABORADORES** contém a lista de todos os colaboradores cadastrados no sistema.
                
                **Colunas:**
                - `id_colaborador`: Identificador único do colaborador
                - `nome_colaborador`: Nome completo do colaborador
                - `cargo`: Cargo/função do colaborador
            """
            )
    else:
        st.error("❌ Aba COLABORADORES não encontrada no arquivo.")

# Tab 2: ALIASES
with core_tabs[1]:
    if "ALIASES" in all_sheets:
        df_aliases = all_sheets["ALIASES"]
        render_sheet_view(df_aliases, "ALIASES")

        with st.expander("ℹ️ Sobre esta aba"):
            st.markdown(
                """
                **ALIASES** contém os aliases (apelidos/variações) de nomes de colaboradores, clientes, etc.
                
                **Colunas:**
                - `entidade`: Tipo de entidade (colaborador, cliente, etc.)
                - `alias`: Nome alternativo/variação
                - `padrao`: Nome padrão/canônico
                
                **Uso:** Quando o sistema encontra o `alias` nos dados, ele o substitui pelo nome `padrao`.
            """
            )
    else:
        st.error("❌ Aba ALIASES não encontrada no arquivo.")

# Tab 3: CARGOS
with core_tabs[2]:
    if "CARGOS" in all_sheets:
        df_cargos = all_sheets["CARGOS"]
        render_sheet_view(df_cargos, "CARGOS")

        with st.expander("ℹ️ Sobre esta aba"):
            st.markdown(
                """
                **CARGOS** contém a lista de cargos/funções disponíveis no sistema.
                
                Esta aba define quais são os cargos válidos que podem ser atribuídos aos colaboradores.
            """
            )
    else:
        st.error("❌ Aba CARGOS não encontrada no arquivo.")

# Tab 4: METAS INDIVIDUAIS
with core_tabs[3]:
    if "METAS_INDIVIDUAIS" in all_sheets:
        df_metas = all_sheets["METAS_INDIVIDUAIS"]
        render_sheet_view(df_metas, "METAS_INDIVIDUAIS")

        with st.expander("ℹ️ Sobre esta aba"):
            st.markdown(
                """
                **METAS_INDIVIDUAIS** contém as metas estabelecidas para cada colaborador.
                
                As metas são utilizadas no cálculo do fator de correção e das comissões.
            """
            )
    else:
        st.error("❌ Aba METAS_INDIVIDUAIS não encontrada no arquivo.")

# Tab 5: CONFIG COMISSÃO
with core_tabs[4]:
    if "CONFIG_COMISSAO" in all_sheets:
        df_config = all_sheets["CONFIG_COMISSAO"]
        render_sheet_view(df_config, "CONFIG_COMISSAO")

        with st.expander("ℹ️ Sobre esta aba"):
            st.markdown(
                """
                **CONFIG_COMISSAO** contém as configurações das regras de comissão por cargo.
                
                Define percentuais, tipos de cálculo e outras regras para cada cargo.
            """
            )
    else:
        st.error("❌ Aba CONFIG_COMISSAO não encontrada no arquivo.")

st.divider()

# --- Outras Abas (Visualização Completa) ---
st.header("📂 Todas as Abas")
st.markdown("Visualize todas as abas disponíveis no arquivo:")

# Lista de todas as abas
all_sheet_names = list(all_sheets.keys())

# Filtrar abas que não estão nas principais
other_sheets = [name for name in all_sheet_names if name not in handler.CORE_SHEETS]

if other_sheets:
    # Criar um selectbox para escolher a aba
    selected_sheet = st.selectbox(
        "Selecione uma aba para visualizar:",
        options=[""] + other_sheets,
        format_func=lambda x: "-- Selecione --" if x == "" else x,
    )

    if selected_sheet:
        st.markdown(f"### 📄 {selected_sheet}")
        df_selected = all_sheets[selected_sheet]
        render_sheet_view(df_selected, selected_sheet)
else:
    st.info("Todas as abas principais foram exibidas acima.")

# --- Footer com Estatísticas ---
st.divider()
st.subheader("📊 Estatísticas Gerais")

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric("📑 Total de Abas", len(all_sheets))

with col2:
    total_rows = sum(len(df) for df in all_sheets.values())
    st.metric("📊 Total de Registros", total_rows)

with col3:
    total_cols = sum(len(df.columns) for df in all_sheets.values())
    st.metric("📝 Total de Colunas", total_cols)

with col4:
    # Abas vazias
    empty_sheets = sum(1 for df in all_sheets.values() if df.empty)
    st.metric("⚠️ Abas Vazias", empty_sheets)

# --- Botão de Atualização ---
st.divider()
col_refresh, col_help = st.columns([1, 3])

with col_refresh:
    if st.button("🔄 Recarregar Dados", use_container_width=True):
        st.cache_data.clear()
        st.rerun()

with col_help:
    st.info(
        "💡 **Dica:** Use o botão 'Recarregar' se você modificou o arquivo externamente."
    )
