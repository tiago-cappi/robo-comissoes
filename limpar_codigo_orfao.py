"""
Script para limpar código órfão deixado pela remoção de _gerar_reconciliacao_detalhada_processo.
"""

# Ler o arquivo
with open('calculo_comissoes.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Ler a função correta do backup
with open('calculo_comissoes_backup_20251029_233238.py', 'r', encoding='utf-8') as f:
    backup_lines = f.readlines()

# Encontrar onde inserir a função correta
for i, line in enumerate(lines):
    if 'def _get_regra_comissao(self, linha, grupo, subgrupo, tipo_mercadoria, cargo):' in line:
        print(f"Encontrado _get_regra_comissao na linha {i+1} do arquivo atual")
        inicio = i
        break

# Encontrar onde está no backup
for i, line in enumerate(backup_lines):
    if 'def _get_regra_comissao(self, linha, grupo, subgrupo, tipo_mercadoria, cargo):' in line:
        print(f"Encontrado _get_regra_comissao na linha {i+1} do backup")
        backup_inicio = i
        # Copiar até a próxima função
        backup_fim = None
        for j in range(backup_inicio + 1, len(backup_lines)):
            if backup_lines[j].strip().startswith('def ') and not backup_lines[j].strip().startswith('def _match'):
                backup_fim = j
                print(f"Próxima função encontrada na linha {j+1} do backup")
                break
        break

if backup_fim is None:
    print("ERRO: Não encontrou próxima função no backup")
    exit(1)

# Copiar a função correta do backup
funcao_correta = backup_lines[backup_inicio:backup_fim]

# Encontrar onde termina no arquivo atual (próxima função def)
fim = None
for j in range(inicio + 1, len(lines)):
    if lines[j].strip().startswith('def _calcular_comissoes'):
        fim = j
        print(f"Próxima função encontrada na linha {j+1} do arquivo atual")
        break

if fim is None:
    print("ERRO: Não encontrou próxima função no arquivo atual")
    exit(1)

# Montar novo arquivo
novas_lines = lines[:inicio] + funcao_correta + ['\n'] + lines[fim:]

# Salvar
with open('calculo_comissoes.py', 'w', encoding='utf-8') as f:
    f.writelines(novas_lines)

print(f"[OK] Removidas {fim - inicio} linhas, inseridas {len(funcao_correta)} linhas")
print("[OK] Código órfão removido!")

