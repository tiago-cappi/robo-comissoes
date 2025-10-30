"""
Componente de navegação lateral.
"""

import streamlit as st


def render_sidebar_navigation():
    """Renderiza a navegação lateral com informações úteis."""

    with st.sidebar:
        st.image("https://img.icons8.com/color/96/000000/money.png", width=80)

        st.title("Robô de Comissões")

        st.markdown("---")

        st.markdown(
            """
            ### 📋 Navegação
            
            Use o menu à esquerda para navegar entre as páginas:
            
            - **🏠 Home** - Visão geral
            - **📋 Regras** - Gerenciar regras
            - **📤 Upload** - Carregar arquivos
            - **⚙️ Processar** - Calcular comissões
            - **📊 Resultados** - Ver resultados
        """
        )

        st.markdown("---")

        st.markdown(
            """
            ### ℹ️ Informações
            
            **Versão:** 1.0.0  
            **Status:** Operacional ✅
        """
        )

        st.markdown("---")

        # Botões de ação rápida
        st.markdown("### ⚡ Ações Rápidas")

        if st.button("🔄 Limpar Cache", use_container_width=True):
            st.cache_data.clear()
            st.success("Cache limpo!")
            st.rerun()

        if st.button("📖 Documentação", use_container_width=True):
            st.info("Documentação em breve!")


def render_page_header(title: str, icon: str, description: str):
    """
    Renderiza o cabeçalho padrão de uma página.

    Args:
        title: Título da página
        icon: Emoji/ícone
        description: Descrição da página
    """
    st.title(f"{icon} {title}")
    st.markdown(description)
    st.divider()
