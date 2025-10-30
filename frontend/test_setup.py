"""
Script de Teste - Verificação da Configuração Inicial

Execute este script para verificar se tudo está configurado corretamente
antes de iniciar o Streamlit.

Uso: python test_setup.py
"""

import sys
from pathlib import Path

# Adicionar frontend ao path
FRONTEND_DIR = Path(__file__).parent
sys.path.insert(0, str(FRONTEND_DIR))


def test_imports():
    """Testa se todos os imports necessários funcionam"""
    print("[*] Testando imports...")

    try:
        import streamlit

        print("  [OK] Streamlit")
    except ImportError as e:
        print(f"  [ERRO] Streamlit - {e}")
        return False

    try:
        import pandas

        print("  [OK] Pandas")
    except ImportError as e:
        print(f"  [ERRO] Pandas - {e}")
        return False

    try:
        import openpyxl

        print("  [OK] OpenPyXL")
    except ImportError as e:
        print(f"  [ERRO] OpenPyXL - {e}")
        return False

    try:
        import plotly

        print("  [OK] Plotly")
    except ImportError as e:
        print(f"  [ERRO] Plotly - {e}")
        return False

    return True


def test_config():
    """Testa se o módulo de configuração funciona"""
    print("\n[*] Testando configuracoes...")

    try:
        from config.settings import (
            PROJECT_ROOT,
            BACKEND_DIR,
            REGRAS_COMISSOES_FILE,
            verificar_backend_disponivel,
        )

        print(f"  [OK] Config importado")
        print(f"  PROJECT_ROOT: {PROJECT_ROOT}")
        print(f"  BACKEND_DIR: {BACKEND_DIR}")
        print(f"  REGRAS_COMISSOES_FILE: {REGRAS_COMISSOES_FILE}")

        # Verificar backend
        backend_ok, faltando = verificar_backend_disponivel()
        if backend_ok:
            print("  [OK] Backend disponivel")
        else:
            print("  [AVISO] Alguns arquivos do backend nao foram encontrados:")
            for arquivo in faltando:
                print(f"      - {arquivo}")

        return True

    except Exception as e:
        print(f"  [ERRO] Erro ao carregar config: {e}")
        return False


def test_structure():
    """Testa se a estrutura de pastas está correta"""
    print("\n[*] Testando estrutura de pastas...")

    required_dirs = [
        "pages",
        "components",
        "utils",
        "config",
        "assets",
        ".streamlit",
    ]

    all_ok = True
    for dir_name in required_dirs:
        dir_path = FRONTEND_DIR / dir_name
        if dir_path.exists():
            print(f"  [OK] {dir_name}/")
        else:
            print(f"  [ERRO] {dir_name}/ - nao encontrada")
            all_ok = False

    return all_ok


def test_files():
    """Testa se os arquivos principais existem"""
    print("\n[*] Testando arquivos principais...")

    required_files = [
        "app_main.py",
        "requirements_frontend.txt",
        "config/settings.py",
        ".streamlit/config.toml",
    ]

    all_ok = True
    for file_name in required_files:
        file_path = FRONTEND_DIR / file_name
        if file_path.exists():
            print(f"  [OK] {file_name}")
        else:
            print(f"  [ERRO] {file_name} - nao encontrado")
            all_ok = False

    return all_ok


def main():
    """Executa todos os testes"""
    print("=" * 60)
    print("TESTE DE CONFIGURACAO - Frontend Robo de Comissoes")
    print("=" * 60)

    results = []

    # Executar testes
    results.append(("Imports", test_imports()))
    results.append(("Estrutura", test_structure()))
    results.append(("Arquivos", test_files()))
    results.append(("Configuração", test_config()))

    # Resumo
    print("\n" + "=" * 60)
    print("RESUMO DOS TESTES")
    print("=" * 60)

    all_passed = True
    for test_name, passed in results:
        status = "[OK] PASSOU" if passed else "[ERRO] FALHOU"
        print(f"{test_name:20} {status}")
        if not passed:
            all_passed = False

    print("=" * 60)

    if all_passed:
        print("\n[OK] TUDO CERTO! O frontend esta pronto para uso.")
        print("\nProximo passo:")
        print("   1. Certifique-se de que as dependencias estao instaladas:")
        print("      pip install -r requirements_frontend.txt")
        print("\n   2. Inicie o Streamlit:")
        print("      streamlit run app_main.py")
        print("\n   3. Acesse no navegador:")
        print("      http://localhost:8501")
        return 0
    else:
        print("\n[AVISO] Alguns testes falharam.")
        print("   Corrija os problemas antes de prosseguir.")
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
