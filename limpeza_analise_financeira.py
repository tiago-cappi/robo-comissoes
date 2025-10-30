import pandas as pd
import re
import os
import sys
import unicodedata
from datetime import datetime

# --- CONFIGURAÇÕES ---
# Nome do arquivo bruto da Análise Financeira
ARQUIVO_BRUTO_ANALISE_FINANCEIRA = "Análise Financeira.xlsx"

# Nome do arquivo de saída, limpo e estruturado
ARQUIVO_SAIDA_LIMPO = "Pagamentos_Regulares_do_Mes.xlsx"
# ---------------------


def _normalize_colname(s):
    """Normaliza nome de coluna para facilitar detecção."""
    if not isinstance(s, str):
        return ""
    s = s.strip().lower()
    s = unicodedata.normalize("NFKD", s)
    s = re.sub(r"[^a-z0-9]+", "_", s)
    return s


def _to_float(v):
    """Converte valor para float de forma segura."""
    if pd.isna(v):
        return None
    if isinstance(v, (int, float)):
        return float(v)
    if isinstance(v, str):
        s = v.strip().replace(",", ".")
        s = re.sub(r"[^\d\.\-]", "", s)
        if not s or s == ".":
            return None
        try:
            return float(s)
        except Exception:
            return None
    return None


def _to_date(v):
    """Converte valor para datetime de forma segura."""
    if pd.isna(v):
        return None
    if isinstance(v, datetime):
        return v
    if isinstance(v, str):
        try:
            return pd.to_datetime(v, dayfirst=True, errors='coerce')
        except Exception:
            return None
    try:
        return pd.to_datetime(v, errors='coerce')
    except Exception:
        return None


def limpar_analise_financeira(mes, ano):
    """
    Limpa e estrutura o arquivo de Análise Financeira.
    
    Filtros aplicados:
    - Tipo de Baixa == 'B' (OBRIGATÓRIO)
    - Data de Baixa == mês/ano informado
    
    Args:
        mes: Mês (1-12)
        ano: Ano (YYYY)
    """
    print(f"Iniciando a limpeza do arquivo: {ARQUIVO_BRUTO_ANALISE_FINANCEIRA}")
    print(f"Filtrando por: {mes:02d}/{ano}")
    
    if not os.path.exists(ARQUIVO_BRUTO_ANALISE_FINANCEIRA):
        print(f"ERRO: O arquivo '{ARQUIVO_BRUTO_ANALISE_FINANCEIRA}' não foi encontrado.")
        sys.exit(1)
    
    try:
        df_bruto = pd.read_excel(ARQUIVO_BRUTO_ANALISE_FINANCEIRA, header=0)
    except Exception as e:
        print(f"ERRO ao ler o arquivo Excel: {e}")
        sys.exit(1)
    
    if df_bruto.empty:
        print("AVISO: arquivo lido, mas sem linhas.")
        df_empty = pd.DataFrame(
            columns=[
                "DOCUMENTO_NORMALIZADO",
                "DOCUMENTO_ORIGINAL",
                "DATA_PAGAMENTO",
                "VALOR_PAGO",
                "ID_CLIENTE",
                "TIPO_PAGAMENTO",
                "FONTE_ORIGINAL"
            ]
        )
        df_empty.to_excel(ARQUIVO_SAIDA_LIMPO, index=False, engine="openpyxl")
        print(f"Arquivo vazio salvo: '{ARQUIVO_SAIDA_LIMPO}'")
        sys.exit(0)
    
    # Normalizar nomes de colunas para facilitar detecção
    orig_cols = list(df_bruto.columns)
    norm_map = {c: _normalize_colname(str(c)) for c in orig_cols}
    df_bruto.rename(columns=norm_map, inplace=True)
    
    cols = list(df_bruto.columns)
    print(f"Colunas detectadas: {cols}")
    
    # Detectar colunas necessárias
    tipo_baixa_col = None
    data_baixa_col = None
    valor_liquido_col = None
    documento_col = None
    cliente_col = None
    
    for c in cols:
        if tipo_baixa_col is None and "tipo" in c and "baixa" in c:
            tipo_baixa_col = c
        if data_baixa_col is None and ("data" in c or "dt" in c) and "baixa" in c:
            data_baixa_col = c
        if valor_liquido_col is None and "valor" in c and ("liquido" in c or "liq" in c or "li_quido" in c):
            valor_liquido_col = c
        if documento_col is None and "documento" in c:
            documento_col = c
        if cliente_col is None and "cliente" in c:
            cliente_col = c
    
    # Validar se todas as colunas foram encontradas
    colunas_faltantes = []
    if tipo_baixa_col is None:
        colunas_faltantes.append("Tipo de Baixa")
    if data_baixa_col is None:
        colunas_faltantes.append("Data de Baixa")
    if valor_liquido_col is None:
        colunas_faltantes.append("Valor Líquido")
    if documento_col is None:
        colunas_faltantes.append("Documento")
    if cliente_col is None:
        colunas_faltantes.append("Cliente")
    
    if colunas_faltantes:
        print(f"ERRO: Colunas não encontradas: {', '.join(colunas_faltantes)}")
        print(f"Colunas disponíveis: {orig_cols}")
        sys.exit(1)
    
    print(f"Colunas identificadas:")
    print(f"  - Tipo de Baixa: '{tipo_baixa_col}'")
    print(f"  - Data de Baixa: '{data_baixa_col}'")
    print(f"  - Valor Líquido: '{valor_liquido_col}'")
    print(f"  - Documento: '{documento_col}'")
    print(f"  - Cliente: '{cliente_col}'")
    
    # Total de registros antes dos filtros
    total_inicial = len(df_bruto)
    print(f"\nTotal de registros no arquivo: {total_inicial}")
    
    # FILTRO 1: Tipo de Baixa == 'B' (OBRIGATÓRIO)
    print("\nAplicando FILTRO 1: Tipo de Baixa == 'B'...")
    df_bruto[tipo_baixa_col] = df_bruto[tipo_baixa_col].astype(str).str.strip().str.upper()
    df_filtrado = df_bruto[df_bruto[tipo_baixa_col] == 'B'].copy()
    excluidos_tipo = total_inicial - len(df_filtrado)
    print(f"  Registros excluídos (Tipo != 'B'): {excluidos_tipo}")
    print(f"  Registros restantes: {len(df_filtrado)}")
    
    if df_filtrado.empty:
        print("AVISO: Nenhum registro com Tipo de Baixa == 'B'.")
        df_empty = pd.DataFrame(
            columns=[
                "DOCUMENTO_NORMALIZADO",
                "DOCUMENTO_ORIGINAL",
                "DATA_PAGAMENTO",
                "VALOR_PAGO",
                "ID_CLIENTE",
                "TIPO_PAGAMENTO",
                "FONTE_ORIGINAL"
            ]
        )
        df_empty.to_excel(ARQUIVO_SAIDA_LIMPO, index=False, engine="openpyxl")
        print(f"Arquivo vazio salvo: '{ARQUIVO_SAIDA_LIMPO}'")
        sys.exit(0)
    
    # FILTRO 2: Data de Baixa (mês/ano)
    print(f"\nAplicando FILTRO 2: Data de Baixa == {mes:02d}/{ano}...")
    df_filtrado[data_baixa_col] = df_filtrado[data_baixa_col].apply(_to_date)
    
    # Remover registros com data inválida
    df_filtrado = df_filtrado[df_filtrado[data_baixa_col].notna()].copy()
    
    # Filtrar por mês e ano
    mask_mes_ano = (
        (df_filtrado[data_baixa_col].dt.month == mes) &
        (df_filtrado[data_baixa_col].dt.year == ano)
    )
    df_filtrado = df_filtrado[mask_mes_ano].copy()
    
    print(f"  Registros após filtro de data: {len(df_filtrado)}")
    
    if df_filtrado.empty:
        print(f"AVISO: Nenhum registro para {mes:02d}/{ano} com Tipo de Baixa == 'B'.")
        df_empty = pd.DataFrame(
            columns=[
                "DOCUMENTO_NORMALIZADO",
                "DOCUMENTO_ORIGINAL",
                "DATA_PAGAMENTO",
                "VALOR_PAGO",
                "ID_CLIENTE",
                "TIPO_PAGAMENTO",
                "FONTE_ORIGINAL"
            ]
        )
        df_empty.to_excel(ARQUIVO_SAIDA_LIMPO, index=False, engine="openpyxl")
        print(f"Arquivo vazio salvo: '{ARQUIVO_SAIDA_LIMPO}'")
        sys.exit(0)
    
    # Processar colunas
    print("\nProcessando dados...")
    
    # IMPORTANTE: Extrair 6 primeiros dígitos do Documento (preservar zeros à esquerda)
    df_filtrado['DOCUMENTO_ORIGINAL'] = df_filtrado[documento_col].astype(str).str.strip()
    df_filtrado['DOCUMENTO_NORMALIZADO'] = df_filtrado['DOCUMENTO_ORIGINAL'].str[:6]
    
    # Converter valor líquido para float
    df_filtrado['VALOR_PAGO'] = df_filtrado[valor_liquido_col].apply(_to_float)
    
    # ID Cliente
    df_filtrado['ID_CLIENTE'] = df_filtrado[cliente_col].astype(str).str.strip()
    
    # Data de pagamento
    df_filtrado['DATA_PAGAMENTO'] = df_filtrado[data_baixa_col]
    
    # Adicionar metadados
    df_filtrado['TIPO_PAGAMENTO'] = 'Pagamento Regular'
    df_filtrado['FONTE_ORIGINAL'] = 'Analise_Financeira'
    
    # Selecionar apenas as colunas finais
    df_limpo = df_filtrado[[
        'DOCUMENTO_NORMALIZADO',
        'DOCUMENTO_ORIGINAL',
        'DATA_PAGAMENTO',
        'VALOR_PAGO',
        'ID_CLIENTE',
        'TIPO_PAGAMENTO',
        'FONTE_ORIGINAL'
    ]].copy()
    
    # Remover registros com valor inválido
    df_limpo = df_limpo[df_limpo['VALOR_PAGO'].notna()].copy()
    df_limpo = df_limpo[df_limpo['VALOR_PAGO'] > 0].copy()
    
    print(f"\nTotal de registros finais: {len(df_limpo)}")
    
    if df_limpo.empty:
        print("AVISO: Nenhum registro válido após processamento.")
        df_empty = pd.DataFrame(
            columns=[
                "DOCUMENTO_NORMALIZADO",
                "DOCUMENTO_ORIGINAL",
                "DATA_PAGAMENTO",
                "VALOR_PAGO",
                "ID_CLIENTE",
                "TIPO_PAGAMENTO",
                "FONTE_ORIGINAL"
            ]
        )
        df_empty.to_excel(ARQUIVO_SAIDA_LIMPO, index=False, engine="openpyxl")
        print(f"Arquivo vazio salvo: '{ARQUIVO_SAIDA_LIMPO}'")
        sys.exit(0)
    
    # Salvar arquivo limpo
    df_limpo.to_excel(ARQUIVO_SAIDA_LIMPO, index=False, engine="openpyxl")
    print(f"\nArquivo salvo com sucesso: '{ARQUIVO_SAIDA_LIMPO}'")
    print(f"Total de pagamentos regulares processados: {len(df_limpo)}")
    
    # Estatísticas
    print("\n=== ESTATÍSTICAS ===")
    print(f"Valor total: R$ {df_limpo['VALOR_PAGO'].sum():,.2f}")
    print(f"Valor médio: R$ {df_limpo['VALOR_PAGO'].mean():,.2f}")
    print(f"Documentos únicos: {df_limpo['DOCUMENTO_NORMALIZADO'].nunique()}")
    print(f"Clientes únicos: {df_limpo['ID_CLIENTE'].nunique()}")


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Uso: python limpeza_analise_financeira.py <mes> <ano>")
        print("Exemplo: python limpeza_analise_financeira.py 10 2024")
        sys.exit(1)
    
    try:
        mes = int(sys.argv[1])
        ano = int(sys.argv[2])
        
        if not (1 <= mes <= 12):
            print("ERRO: Mês deve estar entre 1 e 12")
            sys.exit(1)
        
        if not (2000 <= ano <= 2100):
            print("ERRO: Ano deve estar entre 2000 e 2100")
            sys.exit(1)
        
        limpar_analise_financeira(mes, ano)
        
    except ValueError:
        print("ERRO: Mês e ano devem ser números inteiros")
        sys.exit(1)

