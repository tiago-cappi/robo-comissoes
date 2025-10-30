"""Teste simples dos utilitarios de Excel."""

import sys
from pathlib import Path

FRONTEND_DIR = Path(__file__).parent
sys.path.insert(0, str(FRONTEND_DIR))

from config.settings import REGRAS_COMISSOES_FILE
from utils.excel_handler import RegrasComissoesHandler


def main():
    print("=" * 60)
    print("TESTE SIMPLES - Utilitarios Excel")
    print("=" * 60)

    handler = RegrasComissoesHandler(REGRAS_COMISSOES_FILE)

    # Teste 1: Arquivo existe?
    print("\n[1] Verificando arquivo...")
    if not handler.file_exists():
        print("    ERRO: Arquivo nao encontrado")
        return 1
    print(f"    OK: {REGRAS_COMISSOES_FILE}")

    # Teste 2: Ler abas
    print("\n[2] Lendo abas...")
    sheet_names = handler.get_sheet_names()
    print(f"    Encontradas {len(sheet_names)} abas: {', '.join(sheet_names)}")

    # Teste 3: Ler COLABORADORES
    print("\n[3] Lendo aba COLABORADORES...")
    df_colab = handler.read_colaboradores()
    if df_colab.empty:
        print("    AVISO: Aba vazia")
    else:
        print(f"    OK: {len(df_colab)} linhas")
        print(f"    Colunas: {', '.join(df_colab.columns.tolist())}")
        print(f"    Primeiras linhas:")
        for i, row in df_colab.head(3).iterrows():
            print(f"      - {row.to_dict()}")

    # Teste 4: Ler ALIASES
    print("\n[4] Lendo aba ALIASES...")
    df_aliases = handler.read_aliases()
    if df_aliases.empty:
        print("    AVISO: Aba vazia")
    else:
        print(f"    OK: {len(df_aliases)} linhas")
        print(f"    Colunas: {', '.join(df_aliases.columns.tolist())}")
        print(f"    Exemplo de alias:")
        for i, row in df_aliases.head(2).iterrows():
            print(f"      - {row['entidade']}: '{row['alias']}' -> '{row['padrao']}'")

    print("\n" + "=" * 60)
    print("TODOS OS TESTES PASSARAM!")
    print("=" * 60)

    return 0


if __name__ == "__main__":
    sys.exit(main())
