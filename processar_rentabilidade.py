import pandas as pd
import os

def analisar_rentabilidade(caminho_arquivo):
    """
    Função para ler e analisar a estrutura de um arquivo Excel de rentabilidade.
    """
    if not os.path.exists(caminho_arquivo):
        print(f"Erro: O arquivo '{caminho_arquivo}' não foi encontrado.")
        return

    try:
        # Lendo o arquivo sem cabeçalho para ver a estrutura crua
        df = pd.read_excel(caminho_arquivo, header=None)
        
        print("--- Análise Preliminar do Arquivo de Rentabilidade ---")
        print(f"Arquivo: {caminho_arquivo}")
        print(f"Dimensões do arquivo (linhas, colunas): {df.shape}\n")
        
        print("Amostra das primeiras 30 linhas do arquivo:")
        # Usando to_string() para garantir que todas as colunas sejam exibidas
        print(df.head(30).to_string())
        
    except Exception as e:
        print(f"Ocorreu um erro ao ler o arquivo: {e}")

if __name__ == "__main__":
    # Lê o arquivo correto que está na pasta 'rentabilidades'
    pasta = "rentabilidades"
    # arquivo presente na pasta conforme listagem: 'rentabilidade_realizada_08_2025.xls'
    nome_arquivo_entrada = os.path.join(pasta, "rentabilidade_realizada_08_2025.xls")

    analisar_rentabilidade(nome_arquivo_entrada)
