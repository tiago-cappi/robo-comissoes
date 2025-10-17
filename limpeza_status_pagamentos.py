import pandas as pd
import re
import os

# --- CONFIGURAÇÕES ---
# Nome do arquivo bruto de status de pagamento gerado pelo ERP
ARQUIVO_BRUTO_STATUS = 'fin_adcli_pg_m3.xls'

# Nome do arquivo de saída, limpo e estruturado
ARQUIVO_SAIDA_LIMPO = 'Status_Pagamentos_Processos.xlsx'
# ---------------------


def extrair_processo_status(texto_documento):
    """
    Usa expressões regulares (regex) para encontrar a primeira sequência de números
    em um texto como 'COT140813'. Retorna a sequência de números encontrada.
    """
    if isinstance(texto_documento, str):
        # Remove possíveis sufixos de parcela como '/1', '/2', etc.
        texto_base = texto_documento.split('/')[0]
        # Procura pela primeira sequência contínua de um ou mais dígitos.
        match = re.search(r'\d+', texto_base)
        if match:
            return match.group(0)
    return None


def limpar_dados_status_pagamento():
    """
    Função principal que lê o arquivo bruto de status de pagamento do ERP, 
    extrai as informações relevantes e salva um novo arquivo Excel estruturado.
    """
    print(f"Iniciando a limpeza do arquivo de status de pagamentos: {ARQUIVO_BRUTO_STATUS}")

    if not os.path.exists(ARQUIVO_BRUTO_STATUS):
        print(f"ERRO: O arquivo de entrada '{ARQUIVO_BRUTO_STATUS}' não foi encontrado.")
        return

    try:
        # Lê a planilha inteira sem assumir um cabeçalho, pois o arquivo é um relatório.
        df_bruto = pd.read_excel(ARQUIVO_BRUTO_STATUS, header=None)
    except Exception as e:
        print(f"Ocorreu um erro ao ler o arquivo Excel: {e}")
        return

    # Procura dinamicamente pela primeira linha que marca o início de um bloco de cliente.
    start_index = -1
    for index, row in df_bruto.iterrows():
        # Verifica se a primeira célula é um texto e se começa com 'CLIENTE:'
        if isinstance(row.iloc[0], str) and row.iloc[0].strip().startswith('CLIENTE:'):
            start_index = index
            break
            
    if start_index == -1:
        print("\nAVISO: Nenhuma linha de cliente ('CLIENTE:') foi encontrada para iniciar o processamento.")
        return

    # Corta o DataFrame para começar a partir do primeiro bloco de cliente encontrado.
    df_processar = df_bruto.iloc[start_index:].reset_index(drop=True)

    dados_limpos = []
    processo_bloco_atual = None
    print("Processando linhas do arquivo bruto...")

    # Itera sobre cada linha do arquivo lido
    for index, row in df_processar.iterrows():
        # A primeira coluna nos ajuda a identificar o tipo de linha
        coluna_a = str(row.iloc[0])

        # Se a linha começa com 'CLIENTE:', é um novo bloco. Resetamos a variável de processo.
        if coluna_a.strip().startswith('CLIENTE:'):
            processo_bloco_atual = None
            continue

        # Se a linha começa com 'REC', é uma linha de dados que nos interessa.
        if coluna_a.strip().startswith('REC'):
            # Se ainda não temos um processo para este bloco, extraímos da primeira linha encontrada.
            if processo_bloco_atual is None:
                texto_do_processo = str(row.iloc[1]) # O processo está na segunda coluna
                processo_bloco_atual = extrair_processo_status(texto_do_processo)

            # Se não conseguimos encontrar um processo, esta linha ou bloco é inválido.
            if processo_bloco_atual is None:
                continue

            # Extrai os valores das colunas corretas, usando o índice numérico
            # pois os nomes podem ser ambíguos ('Unnamed: X').
            # Vl. Original está na 8ª coluna (índice 7)
            # Vl. Aberto está na 10ª coluna (índice 9)
            valor_original = row.iloc[7]
            valor_aberto = row.iloc[9]

            # Garante que os valores numéricos são válidos antes de prosseguir
            if pd.isna(valor_original) or pd.isna(valor_aberto):
                continue
            
            # Determina o status com base no valor aberto
            status_pagamento = "Quitado" if float(valor_aberto) == 0.0 else "Em Aberto"

            dados_limpos.append({
                'PROCESSO': str(processo_bloco_atual),
                'VALOR_ORIGINAL': float(valor_original),
                'STATUS_PAGAMENTO': status_pagamento
            })

    if not dados_limpos:
        print("\nAVISO: Nenhuma linha de status de pagamento válida foi encontrada no arquivo de entrada.")
        return

    df_limpo = pd.DataFrame(dados_limpos)
    
    # Como um processo pode aparecer várias vezes (uma para cada parcela),
    # precisamos consolidar para ter um status final único por processo.
    # Se qualquer uma das parcelas estiver "Em Aberto", o status final do processo é "Em Aberto".
    def consolidar_status(series):
        if "Em Aberto" in series.values:
            return "Em Aberto"
        return "Quitado"

    # Agrupamos por processo e aplicamos a lógica de consolidação
    df_final = df_limpo.groupby('PROCESSO').agg(
        VALOR_ORIGINAL=('VALOR_ORIGINAL', 'sum'),
        STATUS_PAGAMENTO=('STATUS_PAGAMENTO', consolidar_status)
    ).reset_index()


    try:
        df_final.to_excel(ARQUIVO_SAIDA_LIMPO, index=False, engine='openpyxl')
        print(f"\nSucesso! Arquivo de status limpo e consolidado foi salvo como: '{ARQUIVO_SAIDA_LIMPO}'")
        print(f"Total de {len(df_final)} processos únicos analisados.")
    except Exception as e:
        print(f"Ocorreu um erro ao salvar o arquivo Excel de saída: {e}")

if __name__ == '__main__':
    limpar_dados_status_pagamento()

