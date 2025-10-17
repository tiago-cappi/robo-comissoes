import pandas as pd
import re
import os

# --- CONFIGURAÇÕES ---
# Nome do arquivo bruto gerado pelo ERP
ARQUIVO_BRUTO_RECEBIMENTOS = 'fin_conci_adcli_m3.xls'

# Nome do arquivo de saída, limpo e estruturado
ARQUIVO_SAIDA_LIMPO = 'Recebimentos_do_Mes.xlsx'
# ---------------------


def extrair_processo(texto_documento):
    """
    Usa expressões regulares (regex) para encontrar a primeira sequência de números
    em um texto como 'COT1349052' ou '0209'.
    Esta função foi tornada mais flexível para capturar qualquer código numérico.
    """
    if isinstance(texto_documento, str):
        # Remove possíveis sufixos de parcela como '/1', '/2', etc.
        texto_base = texto_documento.split('/')[0]
        
        # Procura pela primeira sequência contínua de um ou mais dígitos.
        match = re.search(r'\d+', texto_base)
        if match:
            # Retorna a primeira sequência de números encontrada.
            return match.group(0)
    return None


def limpar_dados_recebimento():
    """
    Função principal que lê o arquivo bruto do ERP, limpa e estrutura os dados,
    e salva um novo arquivo Excel pronto para ser usado pelo robô de comissões.
    """
    print(f"Iniciando a limpeza do arquivo de recebimentos: {ARQUIVO_BRUTO_RECEBIMENTOS}")

    if not os.path.exists(ARQUIVO_BRUTO_RECEBIMENTOS):
        print(f"ERRO: O arquivo de entrada '{ARQUIVO_BRUTO_RECEBIMENTOS}' não foi encontrado.")
        return

    try:
        df_bruto = pd.read_excel(ARQUIVO_BRUTO_RECEBIMENTOS, header=0)
    except Exception as e:
        print(f"Ocorreu um erro ao ler o arquivo Excel: {e}")
        return

    dados_limpos = []
    processo_bloco_atual = None # Variável para armazenar o processo do bloco de cliente atual

    print("Processando linhas do arquivo bruto...")

    # Itera sobre cada linha do arquivo lido
    for index, row in df_bruto.iterrows():
        coluna_documento = row.get('Documento')

        # Se encontrar uma linha de total, ela marca o fim de um bloco de cliente.
        # Resetamos a variável para que na próxima linha de dados um novo processo seja extraído.
        if pd.notna(coluna_documento) and str(coluna_documento).strip().startswith('Total do Cliente:'):
            processo_bloco_atual = None
            continue

        # Se a linha não for de total e a coluna 'Documento' estiver vazia ou for inválida, pule.
        if pd.isna(coluna_documento):
            continue
            
        # Pega os valores das colunas corretas, considerando o deslocamento da leitura.
        valor_recebido = row.get('Vl. Aberto') 
        data_recebimento = row.get('Vl. Original')
        id_cliente = row.get('Entrada')

        # Garante que os dados essenciais de uma linha de pagamento existam.
        if pd.isna(valor_recebido) or pd.isna(data_recebimento) or pd.isna(id_cliente):
            continue
            
        # Se processo_bloco_atual é None, significa que esta é a primeira linha de pagamento
        # de um novo bloco de cliente. Hora de extrair o processo.
        if processo_bloco_atual is None:
            texto_do_processo = row.get('Filial')
            processo_bloco_atual = extrair_processo(str(texto_do_processo))

        # Se, mesmo após a tentativa de extração, não houver processo, a linha é inválida.
        if processo_bloco_atual is None:
            continue

        # Se chegamos até aqui, a linha é válida. Usamos o processo do bloco e coletamos os dados.
        dados_limpos.append({
            'PROCESSO': str(processo_bloco_atual),
            'DATA_RECEBIMENTO': data_recebimento,
            'VALOR_RECEBIDO': float(valor_recebido),
            'ID_CLIENTE': str(int(id_cliente)).zfill(6)
        })

    if not dados_limpos:
        print("\nAVISO: Nenhuma linha de recebimento válida foi encontrada no arquivo de entrada.")
        return

    df_limpo = pd.DataFrame(dados_limpos)
    df_limpo['DATA_RECEBIMENTO'] = pd.to_datetime(df_limpo['DATA_RECEBIMENTO'], errors='coerce')
    df_limpo.dropna(subset=['DATA_RECEBIMENTO'], inplace=True)

    try:
        df_limpo.to_excel(ARQUIVO_SAIDA_LIMPO, index=False, engine='openpyxl')
        print(f"\nSucesso! Arquivo limpo e estruturado foi salvo como: '{ARQUIVO_SAIDA_LIMPO}'")
        print(f"Total de {len(df_limpo)} registros de pagamento processados.")
    except Exception as e:
        print(f"Ocorreu um erro ao salvar o arquivo Excel de saída: {e}")

if __name__ == '__main__':
    limpar_dados_recebimento()

