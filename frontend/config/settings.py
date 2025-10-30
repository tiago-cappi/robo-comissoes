"""
Configurações do Frontend - Robô de Comissões

Este arquivo contém todas as configurações, paths e constantes utilizadas pelo frontend.
IMPORTANTE: Não modifica arquivos do backend, apenas os referencia.
"""

import os
from pathlib import Path

# ==================== PATHS ====================

# Diretório raiz do projeto (pai da pasta frontend)
PROJECT_ROOT = Path(__file__).parent.parent.parent

# Diretório do backend (onde estão os scripts principais)
BACKEND_DIR = PROJECT_ROOT

# Diretório do frontend
FRONTEND_DIR = PROJECT_ROOT / "frontend"

# ==================== ARQUIVOS DO BACKEND ====================

# Arquivo principal de regras de comissões
REGRAS_COMISSOES_FILE = BACKEND_DIR / "Regras_Comissoes.xlsx"

# Scripts do backend
SCRIPT_CALCULO_COMISSOES = BACKEND_DIR / "calculo_comissoes.py"
SCRIPT_PREPARAR_DADOS = BACKEND_DIR / "preparar_dados_mensais.py"
SCRIPT_LIMPEZA_RECEBIMENTOS = BACKEND_DIR / "limpeza_recebimentos.py"
SCRIPT_LIMPEZA_STATUS = BACKEND_DIR / "limpeza_status_pagamentos.py"

# Arquivos de entrada (serão criados via upload ou já existem)
ARQUIVO_ANALISE_COMPLETA = BACKEND_DIR / "Analise_Comercial_Completa.csv"
ARQUIVO_FIN_CONCI = BACKEND_DIR / "fin_conci_adcli_m3.xls"
ARQUIVO_FIN_ADCLI = BACKEND_DIR / "fin_adcli_pg_m3.xls"

# Pasta de rentabilidades
PASTA_RENTABILIDADES = BACKEND_DIR / "rentabilidades"

# ==================== ARQUIVOS GERADOS ====================

# Pasta de backups (será criada se não existir)
BACKUP_DIR = FRONTEND_DIR / "backups"

# Padrão de nome dos arquivos de comissões calculadas
COMISSOES_CALCULADAS_PATTERN = "Comissoes_Calculadas_*.xlsx"
DETALHAMENTO_PDF_PATTERN = "Detalhamento_Comissoes_*.pdf"

# ==================== ABAS DO REGRAS_COMISSOES.XLSX ====================

# Lista de abas esperadas no arquivo de regras
ABAS_REGRAS = [
    "PARAMS",
    "CONFIG_COMISSAO",
    "PESOS_METAS",
    "METAS_APLICACAO",
    "METAS_INDIVIDUAIS",
    "META_RENTABILIDADE",
    "METAS_FORNECEDORES",
    "COLABORADORES",
    "CARGOS",
    "ATRIBUICOES",
    "ALIASES",
    "CROSS_SELLING",
]

# Descrições das abas (para tooltips)
ABAS_DESCRICOES = {
    "PARAMS": "Parâmetros gerais de execução (caps, flags, aliases)",
    "CONFIG_COMISSAO": "Regras de comissão por contexto (linha, grupo, subgrupo, tipo, cargo)",
    "PESOS_METAS": "Pesos dos componentes do Fator de Correção por cargo",
    "METAS_APLICACAO": "Metas por linha e tipo de mercadoria (faturamento/conversão)",
    "METAS_INDIVIDUAIS": "Metas individuais por colaborador",
    "META_RENTABILIDADE": "Metas de rentabilidade por contexto",
    "METAS_FORNECEDORES": "Metas de fornecedores por linha e moeda",
    "COLABORADORES": "Lista de colaboradores e seus cargos",
    "CARGOS": "Metadados dos cargos (tipo, comissão, etc.)",
    "ATRIBUICOES": "Atribuições de gestão por contexto",
    "ALIASES": "Mapeamento de aliases para nomes canônicos",
    "CROSS_SELLING": "Configurações de cross-selling",
}

# ==================== CONFIGURAÇÕES DE VALIDAÇÃO ====================

# Colunas obrigatórias por aba (para validação)
COLUNAS_OBRIGATORIAS = {
    "COLABORADORES": ["nome_colaborador", "cargo"],
    "CARGOS": ["nome_cargo"],
    "CONFIG_COMISSAO": ["linha", "cargo", "taxa_rateio_maximo_pct", "fatia_cargo_pct"],
    "PESOS_METAS": ["cargo"],
}

# ==================== CONFIGURAÇÕES DE UI ====================

# Título da aplicação
APP_TITLE = "🎯 Robô de Comissões"
APP_SUBTITLE = "Sistema de Gerenciamento e Cálculo de Comissões"

# Ícones das páginas
PAGE_ICONS = {
    "home": "🏠",
    "regras": "📋",
    "upload": "📤",
    "processar": "⚙️",
    "resultados": "📊",
    "historico": "📜",
}

# Cores do tema (podem ser usadas em gráficos)
THEME_COLORS = {
    "primary": "#1f77b4",
    "success": "#2ecc71",
    "warning": "#f39c12",
    "danger": "#e74c3c",
    "info": "#3498db",
}

# ==================== CONFIGURAÇÕES DE PROCESSAMENTO ====================

# Número máximo de linhas para preview de tabelas
MAX_PREVIEW_ROWS = 100

# Tamanho máximo de upload (em MB)
MAX_UPLOAD_SIZE_MB = 50

# Formato de data padrão
DATE_FORMAT = "%d/%m/%Y"
DATETIME_FORMAT = "%d/%m/%Y %H:%M:%S"

# ==================== MENSAGENS ====================

MSG_SUCESSO_SALVAMENTO = "✅ Alterações salvas com sucesso!"
MSG_ERRO_SALVAMENTO = "❌ Erro ao salvar alterações: {erro}"
MSG_BACKUP_CRIADO = "💾 Backup criado em: {path}"
MSG_ARQUIVO_NAO_ENCONTRADO = "⚠️ Arquivo não encontrado: {arquivo}"
MSG_VALIDACAO_ERRO = "❌ Erro de validação: {erro}"
MSG_PROCESSAMENTO_INICIADO = "⚙️ Processamento iniciado..."
MSG_PROCESSAMENTO_CONCLUIDO = "✅ Processamento concluído com sucesso!"
MSG_PROCESSAMENTO_ERRO = "❌ Erro no processamento: {erro}"

# ==================== FUNÇÕES AUXILIARES ====================


def criar_pastas_necessarias():
    """Cria pastas necessárias se não existirem"""
    BACKUP_DIR.mkdir(exist_ok=True, parents=True)
    PASTA_RENTABILIDADES.mkdir(exist_ok=True, parents=True)


def verificar_backend_disponivel():
    """Verifica se os arquivos essenciais do backend existem"""
    arquivos_essenciais = [
        REGRAS_COMISSOES_FILE,
        SCRIPT_CALCULO_COMISSOES,
        SCRIPT_PREPARAR_DADOS,
    ]

    faltando = []
    for arquivo in arquivos_essenciais:
        if not arquivo.exists():
            faltando.append(arquivo.name)

    return len(faltando) == 0, faltando


def get_path_relativo(caminho_absoluto):
    """Retorna path relativo ao PROJECT_ROOT para exibição"""
    try:
        return Path(caminho_absoluto).relative_to(PROJECT_ROOT)
    except ValueError:
        return Path(caminho_absoluto)


# Inicialização
criar_pastas_necessarias()
