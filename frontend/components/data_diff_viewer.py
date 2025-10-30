"""
Visualizador de Diferenças entre DataFrames.
Mostra alterações feitas nos dados de forma clara e visual.
"""

import streamlit as st
import pandas as pd
from typing import List, Tuple


def detect_changes(
    df_original: pd.DataFrame, df_edited: pd.DataFrame
) -> List[Tuple[int, str, any, any]]:
    """
    Detecta mudanças entre dois DataFrames.

    Args:
        df_original: DataFrame original
        df_edited: DataFrame editado

    Returns:
        Lista de tuplas (row_idx, column, old_value, new_value)
    """
    changes = []

    # Garantir que os índices são os mesmos
    common_index = df_original.index.intersection(df_edited.index)
    common_columns = df_original.columns.intersection(df_edited.columns)

    for idx in common_index:
        for col in common_columns:
            original_val = df_original.loc[idx, col]
            edited_val = df_edited.loc[idx, col]

            # Comparação cuidadosa (considerando NaN)
            if pd.isna(original_val) and pd.isna(edited_val):
                continue

            if original_val != edited_val:
                changes.append((idx, col, original_val, edited_val))

    return changes


def render_changes_table(changes: List[Tuple[int, str, any, any]]):
    """
    Renderiza as mudanças em uma tabela formatada.

    Args:
        changes: Lista de mudanças detectadas
    """
    if not changes:
        st.info("Nenhuma alteração detectada.")
        return

    # Criar DataFrame das mudanças
    changes_df = pd.DataFrame(
        changes, columns=["Linha", "Coluna", "Valor Antigo", "Valor Novo"]
    )

    # Adicionar coluna de status
    changes_df["Linha"] = changes_df["Linha"] + 1  # Indexação começando em 1

    st.dataframe(
        changes_df,
        use_container_width=True,
        hide_index=True,
        column_config={
            "Linha": st.column_config.NumberColumn("Linha", format="%d"),
            "Coluna": st.column_config.TextColumn("Coluna"),
            "Valor Antigo": st.column_config.TextColumn("❌ Antes"),
            "Valor Novo": st.column_config.TextColumn("✅ Depois"),
        },
    )


def render_changes_summary(changes: List[Tuple[int, str, any, any]]):
    """
    Renderiza um resumo das mudanças.

    Args:
        changes: Lista de mudanças detectadas
    """
    if not changes:
        return

    # Estatísticas
    total_changes = len(changes)
    unique_rows = len(set(change[0] for change in changes))
    unique_cols = len(set(change[1] for change in changes))

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("Total de Alterações", total_changes)

    with col2:
        st.metric("Linhas Afetadas", unique_rows)

    with col3:
        st.metric("Colunas Alteradas", unique_cols)


def render_diff_view(
    df_original: pd.DataFrame, df_edited: pd.DataFrame, show_only_changes: bool = True
):
    """
    Renderiza visualização completa das diferenças.

    Args:
        df_original: DataFrame original
        df_edited: DataFrame editado
        show_only_changes: Se deve mostrar apenas linhas com alterações
    """
    changes = detect_changes(df_original, df_edited)

    if not changes:
        st.success("✅ Nenhuma alteração detectada!")
        return

    # Resumo
    st.markdown("### 📊 Resumo das Alterações")
    render_changes_summary(changes)

    st.markdown("---")

    # Tabela de mudanças
    st.markdown("### 📋 Detalhamento das Alterações")

    # Tabs para diferentes visualizações
    tab_table, tab_diff = st.tabs(["📊 Tabela", "🔍 Diff Visual"])

    with tab_table:
        render_changes_table(changes)

    with tab_diff:
        # Mostrar diff visual
        if show_only_changes:
            # Linhas afetadas
            affected_rows = sorted(set(change[0] for change in changes))

            st.markdown("**Linhas Modificadas:**")

            for row_idx in affected_rows:
                st.markdown(f"#### Linha {row_idx + 1}")

                # Mudanças nesta linha
                row_changes = [c for c in changes if c[0] == row_idx]

                col_before, col_after = st.columns(2)

                with col_before:
                    st.markdown("**❌ Antes:**")
                    for change in row_changes:
                        _, col, old_val, _ = change
                        st.code(f"{col}: {old_val}", language=None)

                with col_after:
                    st.markdown("**✅ Depois:**")
                    for change in row_changes:
                        _, col, _, new_val = change
                        st.code(f"{col}: {new_val}", language=None)

                st.markdown("---")


def render_validation_errors(errors: List[str]):
    """
    Renderiza erros de validação de forma clara.

    Args:
        errors: Lista de mensagens de erro
    """
    if not errors:
        st.success("✅ Validação passou sem erros!")
        return

    st.error(f"❌ {len(errors)} erro(s) de validação encontrado(s):")

    for i, error in enumerate(errors, 1):
        st.markdown(f"{i}. {error}")


def render_confirmation_dialog(
    changes: List[Tuple[int, str, any, any]], on_confirm, on_cancel
):
    """
    Renderiza diálogo de confirmação para salvar alterações.

    Args:
        changes: Lista de mudanças detectadas
        on_confirm: Callback para confirmar
        on_cancel: Callback para cancelar
    """
    st.warning("⚠️ Você está prestes a salvar as seguintes alterações:")

    render_changes_summary(changes)

    st.markdown("---")

    col_confirm, col_cancel = st.columns(2)

    with col_confirm:
        if st.button(
            "✅ Confirmar e Salvar",
            use_container_width=True,
            type="primary",
        ):
            on_confirm()

    with col_cancel:
        if st.button("❌ Cancelar", use_container_width=True):
            on_cancel()
