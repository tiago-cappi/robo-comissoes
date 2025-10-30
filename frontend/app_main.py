"""
Aplicação Principal - Frontend do Robô de Comissões

Este é o ponto de entrada da aplicação Streamlit.
Para executar: streamlit run app_main.py
"""

import streamlit as st
from pathlib import Path
import sys

# Adicionar o diretório do frontend ao path para imports
FRONTEND_DIR = Path(__file__).parent
if str(FRONTEND_DIR) not in sys.path:
    sys.path.insert(0, str(FRONTEND_DIR))

from config.settings import (
    APP_TITLE,
    APP_SUBTITLE,
    PROJECT_ROOT,
    verificar_backend_disponivel,
)

# ==================== CONFIGURAÇÃO DA PÁGINA ====================

st.set_page_config(
    page_title=APP_TITLE,
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        "Get Help": None,
        "Report a bug": None,
        "About": f"# {APP_TITLE}\n\n{APP_SUBTITLE}\n\nVersão 1.0.0",
    },
)

# ==================== ESTILOS CUSTOMIZADOS ====================

st.markdown(
    """
    <style>
        /* Estilo do título principal */
        .main-title {
            font-size: 2.5rem;
            font-weight: bold;
            color: #1f77b4;
            margin-bottom: 0.5rem;
        }
        
        /* Estilo do subtítulo */
        .main-subtitle {
            font-size: 1.2rem;
            color: #666;
            margin-bottom: 2rem;
        }
        
        /* Cards de informação */
        .info-card {
            padding: 1.5rem;
            border-radius: 0.5rem;
            background-color: #f0f2f6;
            margin: 1rem 0;
        }
        
        /* Destaque de métricas */
        .metric-card {
            text-align: center;
            padding: 1rem;
            border-radius: 0.5rem;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
        }
        
        /* Badges de status */
        .badge-success {
            background-color: #2ecc71;
            color: white;
            padding: 0.25rem 0.75rem;
            border-radius: 1rem;
            font-size: 0.85rem;
            font-weight: bold;
        }
        
        .badge-warning {
            background-color: #f39c12;
            color: white;
            padding: 0.25rem 0.75rem;
            border-radius: 1rem;
            font-size: 0.85rem;
            font-weight: bold;
        }
        
        .badge-error {
            background-color: #e74c3c;
            color: white;
            padding: 0.25rem 0.75rem;
            border-radius: 1rem;
            font-size: 0.85rem;
            font-weight: bold;
        }
        
        /* Esconder menu do Streamlit */
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        
        /* Ajustes no sidebar */
        .css-1d391kg {
            padding-top: 1rem;
        }
    </style>
    """,
    unsafe_allow_html=True,
)

# ==================== SIDEBAR ====================

with st.sidebar:
    st.markdown(f"# {APP_TITLE}")
    st.markdown("---")

    # Verificação do backend
    st.markdown("### 🔍 Status do Sistema")
    backend_ok, arquivos_faltando = verificar_backend_disponivel()

    if backend_ok:
        st.success("✅ Backend configurado")
    else:
        st.error("❌ Arquivos faltando:")
        for arquivo in arquivos_faltando:
            st.write(f"- {arquivo}")

    st.markdown("---")

    # Informações do projeto
    st.markdown("### 📂 Diretório do Projeto")
    st.code(str(PROJECT_ROOT), language="text")

    st.markdown("---")

    # Navegação rápida
    st.markdown("### 🧭 Navegação Rápida")
    st.markdown(
        """
    - 📋 **[Regras](?page=regras)** - Editar regras de comissões
    - 📤 **[Upload](?page=upload)** - Carregar arquivos
    - ⚙️ **[Processar](?page=processar)** - Executar cálculos
    - 📊 **[Resultados](?page=resultados)** - Ver relatórios
    """
    )

    st.markdown("---")

    # Informações de versão
    st.caption("Versão 1.0.0 | Outubro 2025")

# ==================== CONTEÚDO PRINCIPAL ====================

# Cabeçalho
st.markdown(f'<div class="main-title">{APP_TITLE}</div>', unsafe_allow_html=True)
st.markdown(f'<div class="main-subtitle">{APP_SUBTITLE}</div>', unsafe_allow_html=True)

# Verificação inicial
if not backend_ok:
    st.error(
        "⚠️ **Atenção:** Alguns arquivos essenciais do backend não foram encontrados. "
        "Verifique a instalação antes de prosseguir."
    )
    st.info(
        "**Arquivos faltando:**\n" + "\n".join([f"- {f}" for f in arquivos_faltando])
    )
    st.stop()

# Bem-vindo
st.markdown("## 👋 Bem-vindo!")

st.markdown(
    """
    Este sistema permite gerenciar todo o processo de cálculo de comissões de forma 
    simples e visual. Escolha uma das opções abaixo para começar:
    """
)

# Cards de funcionalidades principais
col1, col2 = st.columns(2)

with col1:
    st.markdown("### 📋 Gerenciar Regras")
    st.markdown(
        """
        Edite as regras de comissão, metas, colaboradores e todas as configurações 
        do sistema de forma interativa.
        
        - ✏️ Edição inline de tabelas
        - ➕ Adicionar novos registros
        - 🗑️ Remover registros
        - 💾 Backup automático
        """
    )
    if st.button("📋 Ir para Regras", use_container_width=True, type="primary"):
        st.info("👉 Use o menu lateral para navegar até a página 'Regras Comissões'")

with col2:
    st.markdown("### 📤 Processar Comissões")
    st.markdown(
        """
        Faça upload dos arquivos de dados e execute o cálculo de comissões 
        de forma automatizada.
        
        - 📁 Upload de arquivos
        - ⚙️ Processamento automático
        - 📊 Visualização de resultados
        - 📥 Download de relatórios
        """
    )
    if st.button("⚙️ Ir para Processamento", use_container_width=True, type="primary"):
        st.info("👉 Use o menu lateral para navegar até a página 'Processar'")

st.markdown("---")

# Instruções rápidas
with st.expander("📖 Como usar este sistema", expanded=False):
    st.markdown(
        """
        ### Passo a Passo
        
        #### 1️⃣ Configurar Regras (Opcional)
        - Acesse a página **📋 Regras Comissões**
        - Edite as configurações conforme necessário
        - Salve as alterações
        
        #### 2️⃣ Upload de Dados
        - Acesse a página **📤 Upload Arquivos**
        - Faça upload dos 3 arquivos principais:
          - Análise Comercial Completa
          - fin_conci_adcli_m3
          - fin_adcli_pg_m3
        - Valide os dados carregados
        
        #### 3️⃣ Processar
        - Acesse a página **⚙️ Processar**
        - Selecione o mês e ano
        - Execute o cálculo
        - Acompanhe o progresso
        
        #### 4️⃣ Visualizar Resultados
        - Acesse a página **📊 Resultados**
        - Explore as tabelas e gráficos
        - Baixe os relatórios gerados
        
        ### 💡 Dicas
        
        - Todas as alterações em regras criam backup automático
        - Você pode reverter alterações a qualquer momento
        - Os dados são validados antes de serem salvos
        - O sistema não modifica o código do backend
        """
    )

# Métricas de status (exemplo)
st.markdown("## 📊 Status Atual")

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric(
        label="Backend",
        value="OK" if backend_ok else "Erro",
        delta="Operacional" if backend_ok else "Verifique arquivos",
    )

with col2:
    st.metric(
        label="Regras Configuradas",
        value="12 abas",
        delta="Todas carregadas",
    )

with col3:
    st.metric(
        label="Arquivos Pendentes",
        value="0",
        delta="Pronto para processar",
    )

with col4:
    st.metric(
        label="Última Execução",
        value="--",
        delta="Nenhuma ainda",
    )

# Rodapé
st.markdown("---")
st.markdown(
    """
    <div style='text-align: center; color: #666; font-size: 0.9rem;'>
        🎯 Robô de Comissões v1.0.0 | Sistema de Gerenciamento de Comissões de Vendas
    </div>
    """,
    unsafe_allow_html=True,
)
