"""
Script para executar todos os testes do projeto.

Uso:
    python run_tests.py                    # Executa todos os testes
    python run_tests.py --refactored       # Executa apenas os testes da nova lógica
    python run_tests.py --all              # Executa todos os testes (padrão)
"""

import sys
import os

# Garantir que estamos no diretório raiz
os.chdir(os.path.dirname(os.path.abspath(__file__)))

def run_test_file(test_file):
    """Executa um arquivo de teste."""
    print(f"\n{'='*70}")
    print(f"Executando: {test_file}")
    print('='*70)
    
    import subprocess
    result = subprocess.run(
        [sys.executable, test_file],
        cwd=os.path.dirname(os.path.abspath(__file__)),
        capture_output=False
    )
    
    return result.returncode == 0

def main():
    """Função principal."""
    import argparse
    parser = argparse.ArgumentParser(description='Executar testes do robô de comissões')
    parser.add_argument('--refactored', action='store_true', 
                       help='Executar apenas testes da nova lógica refatorada')
    parser.add_argument('--all', action='store_true', default=True,
                       help='Executar todos os testes (padrão)')
    
    args = parser.parse_args()
    
    # Lista de todos os arquivos de teste
    test_files = [
        'tests/test_commission_flow_refactored.py',
        'tests/test_process_state.py',
        'tests/test_payment_services.py',
        'tests/test_reconciliation_services.py',
        'tests/test_utils_column_finder.py',
        'tests/test_utils_date_parser.py',
        'tests/test_utils_normalization.py',
    ]
    
    if args.refactored:
        test_files = ['tests/test_commission_flow_refactored.py']
    
    print("\n" + "="*70)
    print("EXECUTANDO TESTES DO ROBÔ DE COMISSÕES")
    print("="*70)
    
    results = {}
    for test_file in test_files:
        if os.path.exists(test_file):
            success = run_test_file(test_file)
            results[test_file] = success
        else:
            print(f"\n[AVISO] Arquivo não encontrado: {test_file}")
            results[test_file] = False
    
    # Resumo final
    print("\n" + "="*70)
    print("RESUMO DOS TESTES")
    print("="*70)
    
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    for test_file, success in results.items():
        status = "✓ PASSOU" if success else "✗ FALHOU"
        print(f"{status:10} - {test_file}")
    
    print("\n" + "="*70)
    print(f"Total: {passed}/{total} arquivos de teste passaram")
    print("="*70)
    
    if passed == total:
        print("\n🎉 Todos os testes passaram com sucesso!")
        return 0
    else:
        print(f"\n⚠️  {total - passed} arquivo(s) de teste falharam")
        return 1

if __name__ == "__main__":
    sys.exit(main())

