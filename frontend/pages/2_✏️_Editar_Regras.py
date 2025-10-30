"""
Página de Edição de Regras de Comissões.
Permite editar as informações do arquivo Regras_Comissoes.xlsx de forma interativa.
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
from utils.data_validator import RegrasComissoesValidator

# --- Configuração da Página ---
st.set_page_config(
    page_title="Editar Regras",
    page_icon="✏️",
    layout="wide",
)

# --- Título ---
st.title("✏️ Editar Regras de Comissões")
st.markdown(
    """
    Edite as regras de comissões diretamente nas tabelas interativas.
    As alterações serão validadas antes de serem salvas.
"""
)

st.divider()


# --- Abas Editáveis ---
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


def create_backup(file_path: Path) -> Path:
    """Cria um backup do arquivo antes de salvar."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_name = f"{file_path.stem}_backup_{timestamp}{file_path.suffix}"
    backup_path = BACKUP_DIR / backup_name

    # Copiar arquivo
    import shutil

    shutil.copy2(file_path, backup_path)

    return backup_path


def validate_edited_data(df: pd.DataFrame, sheet_name: str) -> tuple[bool, list[str]]:
    """
    Valida os dados editados antes de salvar.

    Returns:
        (is_valid, error_messages)
    """
    errors = []

    # Validação básica
    if df.empty:
        errors.append("O DataFrame está vazio")
        return False, errors

    # Validações específicas por aba
    if sheet_name == "COLABORADORES":
        # Verificar colunas obrigatórias
        required_cols = ["id_colaborador", "nome_colaborador", "cargo"]
        missing_cols = [col for col in required_cols if col not in df.columns]
        if missing_cols:
            errors.append(f"Colunas faltando: {', '.join(missing_cols)}")

        # Verificar valores vazios
        if "nome_colaborador" in df.columns:
            empty_names = df["nome_colaborador"].isna().sum()
            if empty_names > 0:
                errors.append(f"{empty_names} colaboradores sem nome")

        # Verificar IDs duplicados
        if "id_colaborador" in df.columns:
            duplicated_ids = df["id_colaborador"].duplicated().sum()
            if duplicated_ids > 0:
                errors.append(f"{duplicated_ids} IDs duplicados")

    elif sheet_name == "ALIASES":
        # Verificar colunas obrigatórias
        required_cols = ["entidade", "alias", "padrao"]
        missing_cols = [col for col in required_cols if col not in df.columns]
        if missing_cols:
            errors.append(f"Colunas faltando: {', '.join(missing_cols)}")

        # Verificar valores vazios em padrao
        if "padrao" in df.columns:
            empty_padrao = df["padrao"].isna().sum()
            if empty_padrao > 0:
                errors.append(f"{empty_padrao} aliases sem valor padrão")

    elif sheet_name == "CARGOS":
        # Verificar se há pelo menos um cargo
        if len(df) == 0:
            errors.append("Deve haver pelo menos um cargo cadastrado")

    elif sheet_name == "METAS_INDIVIDUAIS":
        # Verificar valores numéricos
        numeric_cols = ["valor", "peso"]
        for col in numeric_cols:
            if col in df.columns:
                try:
                    pd.to_numeric(df[col], errors="raise")
                except (ValueError, TypeError):
                    errors.append(f"Coluna '{col}' contém valores não numéricos")

    return len(errors) == 0, errors


def render_editable_sheet(df: pd.DataFrame, sheet_name: str, key_prefix: str):
    """
    Renderiza uma aba editável com validação.

    Returns:
        DataFrame editado ou None se não houve edição
    """

    if df.empty:
        st.warning(f"⚠️ A aba '{sheet_name}' está vazia.")
        st.info("💡 Use a próxima página para adicionar novos registros.")
        return None

    # Informações
    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("📊 Linhas", len(df))

    with col2:
        st.metric("📝 Colunas", len(df.columns))

    with col3:
        empty_count = df.isna().sum().sum()
        st.metric("⚠️ Células Vazias", empty_count)

    st.markdown("---")

    # Configurações de edição
    with st.expander("⚙️ Configurações de Edição", expanded=False):
        col_config1, col_config2 = st.columns(2)

        with col_config1:
            disabled_cols = st.multiselect(
                "Colunas bloqueadas (não editáveis):",
                options=df.columns.tolist(),
                default=["id_colaborador"] if "id_colaborador" in df.columns else [],
                key=f"{key_prefix}_disabled",
                help="Selecione as colunas que não devem ser editadas",
            )

        with col_config2:
            # Ajustar min_value para não exceder o tamanho do DataFrame
            min_rows = min(10, len(df))
            num_rows = st.number_input(
                "Linhas para exibir:",
                min_value=min_rows,
                max_value=len(df),
                value=min(50, len(df)),
                step=10,
                key=f"{key_prefix}_rows",
            )

    # Editor de dados
    st.markdown("### 📝 Tabela Editável")
    st.info(
        "💡 **Dica:** Clique duas vezes em uma célula para editá-la. "
        "Use Tab para navegar entre células."
    )

    # Configurar colunas editáveis
    column_config = {}
    for col in df.columns:
        if col in disabled_cols:
            column_config[col] = st.column_config.TextColumn(
                col, disabled=True, help=f"Coluna bloqueada: {col}"
            )

    # Data editor
    edited_df = st.data_editor(
        df.head(num_rows),
        use_container_width=True,
        num_rows="fixed",  # Não permite adicionar/remover linhas aqui
        column_config=column_config,
        key=f"{key_prefix}_editor",
        height=400,
    )

    # Detectar mudanças
    if not edited_df.equals(df.head(num_rows)):
        st.warning("⚠️ Você fez alterações nesta tabela!")

        # Mostrar diferenças
        with st.expander("🔍 Ver Alterações", expanded=True):
            changes_detected = False

            for idx in edited_df.index:
                for col in edited_df.columns:
                    original_val = df.loc[idx, col]
                    edited_val = edited_df.loc[idx, col]

                    # Comparação cuidadosa (considerando NaN)
                    if pd.isna(original_val) and pd.isna(edited_val):
                        continue

                    if original_val != edited_val:
                        changes_detected = True
                        st.markdown(
                            f"**Linha {idx + 1}, Coluna `{col}`:**  \n"
                            f"  - Antes: `{original_val}`  \n"
                            f"  - Depois: `{edited_val}`"
                        )

            if not changes_detected:
                st.info("Nenhuma alteração detectada.")

        # Botões de ação
        col_save, col_cancel = st.columns(2)

        with col_save:
            if st.button(
                "💾 Salvar Alterações",
                key=f"{key_prefix}_save",
                use_container_width=True,
                type="primary",
            ):
                # Validar dados
                is_valid, errors = validate_edited_data(edited_df, sheet_name)

                if is_valid:
                    # Atualizar o DataFrame completo com as linhas editadas
                    df_updated = df.copy()
                    df_updated.update(edited_df)

                    return df_updated
                else:
                    st.error("❌ Erros de validação encontrados:")
                    for error in errors:
                        st.write(f"- {error}")
                    return None

        with col_cancel:
            if st.button(
                "🔄 Cancelar",
                key=f"{key_prefix}_cancel",
                use_container_width=True,
            ):
                st.cache_data.clear()
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

# --- Seleção de Aba para Editar ---
st.header("📑 Selecione a Aba para Editar")

# Ícones para cada aba
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
    "Escolha a aba que deseja editar:",
    options=EDITABLE_SHEETS,
    format_func=lambda x: f"{sheet_icons.get(x, '📄')} {x}",
)

st.divider()

# --- Editar Aba Selecionada ---
if selected_sheet:
    st.subheader(f"✏️ Editando: {selected_sheet}")

    df_to_edit = all_sheets[selected_sheet]

    # Renderizar editor
    updated_df = render_editable_sheet(df_to_edit, selected_sheet, selected_sheet)

    # Se houve atualização, salvar
    if updated_df is not None:
        with st.spinner("Salvando alterações..."):
            try:
                # Criar backup
                backup_path = create_backup(REGRAS_COMISSOES_FILE)
                st.success(f"✅ Backup criado: `{backup_path.name}`")

                # Salvar alterações
                success = handler.write_sheet(updated_df, selected_sheet, mode="update")

                if success:
                    st.success("✅ Alterações salvas com sucesso!")
                    st.balloons()

                    # Limpar cache para recarregar dados
                    st.cache_data.clear()

                    # Aguardar um pouco para o usuário ver a mensagem
                    import time

                    time.sleep(2)

                    # Recarregar
                    st.rerun()
                else:
                    st.error("❌ Erro ao salvar alterações.")

            except Exception as e:
                st.error(f"❌ Erro ao salvar: {e}")

# --- Informações de Ajuda ---
st.divider()

with st.expander("ℹ️ Como Usar Esta Página", expanded=False):
    st.markdown(
        """
        ### 📝 Como Editar
        
        1. **Selecione a aba** que deseja editar no menu acima
        2. **Clique duas vezes** em uma célula para editá-la
        3. **Use Tab** para navegar entre células
        4. **Faça suas alterações** diretamente na tabela
        5. **Clique em "Salvar"** para confirmar as alterações
        
        ### 🔒 Colunas Bloqueadas
        
        Algumas colunas (como IDs) são bloqueadas por padrão para evitar
        alterações acidentais. Você pode desbloquear nas configurações.
        
        ### ✅ Validação
        
        Antes de salvar, o sistema valida:
        - Colunas obrigatórias presentes
        - Valores numéricos em colunas numéricas
        - IDs únicos (sem duplicatas)
        - Campos obrigatórios preenchidos
        
        ### 💾 Backup Automático
        
        Sempre que você salva alterações, um backup automático é criado
        na pasta `frontend/backups/` com timestamp.
        
        ### ⚠️ Limitações
        
        - Não é possível adicionar/remover linhas nesta página
        - Para adicionar novos registros, use a página "Adicionar/Remover"
        - Máximo de 50 linhas exibidas por vez (configurável)
    """
    )

# --- Botões de Ação Rápida ---
st.divider()
col_refresh, col_backups = st.columns(2)

with col_refresh:
    if st.button("🔄 Recarregar Dados", use_container_width=True):
        st.cache_data.clear()
        st.rerun()

with col_backups:
    if st.button("📁 Ver Backups", use_container_width=True):
        st.info(f"Backups salvos em: `{BACKUP_DIR}`")

        # Listar backups
        if BACKUP_DIR.exists():
            backups = sorted(BACKUP_DIR.glob("*.xlsx"), reverse=True)
            if backups:
                st.write(f"**{len(backups)} backups encontrados:**")
                for backup in backups[:5]:  # Mostrar últimos 5
                    st.write(f"- {backup.name}")
            else:
                st.write("Nenhum backup encontrado.")
