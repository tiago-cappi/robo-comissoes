"""
Componente para visualização elegante de DataFrames.
"""

import streamlit as st
import pandas as pd
from typing import Optional, List


def render_dataframe_with_stats(
    df: pd.DataFrame,
    title: str,
    key_prefix: str,
    show_download: bool = True,
    height: int = 400,
    description: Optional[str] = None,
):
    """
    Renderiza um DataFrame com estatísticas e opções de visualização.

    Args:
        df: DataFrame a ser exibido
        title: Título da seção
        key_prefix: Prefixo para chaves únicas do Streamlit
        show_download: Se deve mostrar botão de download
        height: Altura da tabela em pixels
        description: Descrição opcional
    """

    st.subheader(title)

    if description:
        st.markdown(description)

    if df.empty:
        st.warning("⚠️ Não há dados para exibir.")
        return

    # Estatísticas
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("📊 Linhas", len(df))

    with col2:
        st.metric("📝 Colunas", len(df.columns))

    with col3:
        empty_cells = df.isna().sum().sum()
        st.metric("⚠️ Vazias", empty_cells)

    with col4:
        duplicates = df.duplicated().sum()
        st.metric("🔄 Duplicadas", duplicates)

    st.markdown("---")

    # Opções de visualização
    col_view1, col_view2 = st.columns([3, 1])

    with col_view2:
        # Filtro de colunas
        show_all = st.checkbox(
            "Todas as colunas", value=True, key=f"{key_prefix}_show_all"
        )

        # Filtro de linhas
        num_rows = st.number_input(
            "Linhas para exibir",
            min_value=1,
            max_value=len(df),
            value=min(100, len(df)),
            step=10,
            key=f"{key_prefix}_num_rows",
        )

    # Seleção de colunas
    if not show_all:
        selected_cols = st.multiselect(
            "Selecione as colunas:",
            options=df.columns.tolist(),
            default=df.columns.tolist()[:5],
            key=f"{key_prefix}_cols",
        )
    else:
        selected_cols = df.columns.tolist()

    # Exibir DataFrame
    if selected_cols:
        display_df = df[selected_cols].head(num_rows)

        st.dataframe(
            display_df,
            use_container_width=True,
            height=height,
        )

        # Informação sobre linhas exibidas
        if num_rows < len(df):
            st.info(
                f"ℹ️ Mostrando {num_rows} de {len(df)} linhas. Ajuste o filtro acima para ver mais."
            )

    else:
        st.warning("⚠️ Selecione pelo menos uma coluna para visualizar.")

    # Botão de download
    if show_download and selected_cols:
        st.download_button(
            label="📥 Baixar como CSV",
            data=df.to_csv(index=False).encode("utf-8"),
            file_name=f"{title.replace(' ', '_')}.csv",
            mime="text/csv",
            key=f"{key_prefix}_download",
        )


def render_dataframe_summary(df: pd.DataFrame, title: str):
    """
    Renderiza um resumo estatístico do DataFrame.

    Args:
        df: DataFrame a ser analisado
        title: Título da seção
    """

    st.subheader(f"📈 Resumo: {title}")

    if df.empty:
        st.warning("⚠️ DataFrame vazio.")
        return

    # Tabs para diferentes visualizações
    tab_info, tab_desc, tab_types, tab_nulls = st.tabs(
        ["ℹ️ Info", "📊 Estatísticas", "🔤 Tipos", "⚠️ Valores Nulos"]
    )

    with tab_info:
        col1, col2 = st.columns(2)

        with col1:
            st.metric("Total de Linhas", len(df))
            st.metric("Total de Colunas", len(df.columns))

        with col2:
            memory_usage = df.memory_usage(deep=True).sum() / 1024 / 1024
            st.metric("Uso de Memória", f"{memory_usage:.2f} MB")

            duplicates = df.duplicated().sum()
            st.metric("Linhas Duplicadas", duplicates)

        st.markdown("**Colunas:**")
        st.write(", ".join(df.columns.tolist()))

    with tab_desc:
        # Estatísticas descritivas apenas para colunas numéricas
        numeric_df = df.select_dtypes(include=["number"])

        if not numeric_df.empty:
            st.dataframe(numeric_df.describe(), use_container_width=True)
        else:
            st.info("Não há colunas numéricas para exibir estatísticas.")

    with tab_types:
        # Tipos de dados
        types_df = pd.DataFrame(
            {
                "Coluna": df.columns,
                "Tipo": df.dtypes.astype(str),
                "Não-Nulos": df.count(),
                "Nulos": df.isna().sum(),
            }
        )

        st.dataframe(types_df, use_container_width=True, height=300)

    with tab_nulls:
        # Análise de valores nulos
        null_counts = df.isna().sum()
        null_pcts = (null_counts / len(df) * 100).round(2)

        nulls_df = pd.DataFrame(
            {
                "Coluna": df.columns,
                "Valores Nulos": null_counts,
                "Percentual (%)": null_pcts,
            }
        )

        # Filtrar apenas colunas com nulos
        nulls_df = nulls_df[nulls_df["Valores Nulos"] > 0]

        if not nulls_df.empty:
            st.dataframe(nulls_df, use_container_width=True, height=300)
        else:
            st.success("✅ Não há valores nulos no DataFrame!")


def render_column_info(df: pd.DataFrame, column_name: str):
    """
    Renderiza informações detalhadas sobre uma coluna específica.

    Args:
        df: DataFrame contendo a coluna
        column_name: Nome da coluna
    """

    if column_name not in df.columns:
        st.error(f"❌ Coluna '{column_name}' não encontrada.")
        return

    col_data = df[column_name]

    st.subheader(f"🔍 Análise da Coluna: {column_name}")

    # Métricas
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Tipo", str(col_data.dtype))

    with col2:
        non_null = col_data.count()
        st.metric("Não-Nulos", non_null)

    with col3:
        null_count = col_data.isna().sum()
        st.metric("Nulos", null_count)

    with col4:
        unique_count = col_data.nunique()
        st.metric("Valores Únicos", unique_count)

    st.markdown("---")

    # Valores mais frequentes
    if unique_count > 0 and unique_count <= 50:
        st.markdown("**📊 Valores Únicos:**")
        value_counts = col_data.value_counts().head(20)

        col_chart, col_table = st.columns(2)

        with col_chart:
            st.bar_chart(value_counts)

        with col_table:
            st.dataframe(
                pd.DataFrame(
                    {"Valor": value_counts.index, "Contagem": value_counts.values}
                ),
                use_container_width=True,
                height=300,
            )

    # Estatísticas para colunas numéricas
    if pd.api.types.is_numeric_dtype(col_data):
        st.markdown("**📈 Estatísticas Numéricas:**")

        stats_col1, stats_col2, stats_col3, stats_col4 = st.columns(4)

        with stats_col1:
            st.metric("Média", f"{col_data.mean():.2f}")

        with stats_col2:
            st.metric("Mediana", f"{col_data.median():.2f}")

        with stats_col3:
            st.metric("Mínimo", f"{col_data.min():.2f}")

        with stats_col4:
            st.metric("Máximo", f"{col_data.max():.2f}")
