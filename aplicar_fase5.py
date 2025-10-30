"""
Script para aplicar modificações da FASE 5 no calculo_comissoes.py

Este script faz backup e aplica as substituições de forma segura.
"""

import os
import shutil
from datetime import datetime

def fazer_backup():
    """Faz backup do arquivo original."""
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_name = f'calculo_comissoes_backup_{timestamp}.py'
    shutil.copy('calculo_comissoes.py', backup_name)
    print(f"[OK] Backup criado: {backup_name}")
    return backup_name

def substituir_aplicar_adiantamentos():
    """Substitui a função _aplicar_adiantamentos_recebimentos."""
    
    novo_conteudo = '''    def _aplicar_adiantamentos_recebimentos(self):
        """
        Calcula e aplica adiantamentos de comissão baseados nos recebimentos do mês.
        
        REFATORADO (FASE 3): Usa PaymentProcessor para processar recebimentos.
        
        Estratégia:
        - Mapeia recebimentos para processos da análise comercial
        - Identifica colaboradores que recebem por recebimento
        - Calcula comissões (valor × taxa × PE, FC=1.0 para recebimentos)
        - Atualiza estado dos processos (valor pago, comissão adiantada)
        """
        _debug("[DEBUG] Aplicando adiantamentos de recebimentos usando PaymentProcessor...")
        
        # Verificar se há recebimentos
        if 'RECEBIMENTOS' not in self.data or self.data['RECEBIMENTOS'].empty:
            _debug("[DEBUG] Nenhum recebimento encontrado.")
            self.comissoes_recebimento_df = pd.DataFrame()
            return
        
        try:
            # Setup do PaymentCommissionCalculator
            calculator = PaymentCommissionCalculator(
                commission_rules_instance=self,  # self tem _get_regra_comissao
                colaboradores_df=self.data.get('COLABORADORES', pd.DataFrame()),
                atribuicoes_df=self.data.get('ATRIBUICOES', pd.DataFrame()),
                recebe_por_recebimento_names=self.recebe_por_recebimento,
                log_callback=self._log_validacao
            )
            
            # Setup do PaymentProcessor
            processor = PaymentProcessor(
                recebimentos_df=self.data['RECEBIMENTOS'],
                analise_comercial_df=self.data.get('ANALISE_COMERCIAL_COMPLETA', pd.DataFrame()),
                state_manager=self.state_manager,
                commission_calculator=calculator,
                log_callback=self._log_validacao
            )
            
            # Processar todos os recebimentos
            comissoes_df, log_mapping = processor.process_all_payments()
            
            self.comissoes_recebimento_df = comissoes_df
            
            # Log resumo
            summary = processor.get_processing_summary()
            _info(f"[Recebimentos] Processados: {summary['pagamentos_mapeados']}/{summary['total_pagamentos']}")
            _info(f"[Recebimentos] Taxa de mapeamento: {summary['taxa_mapeamento']:.1f}%")
            _info(f"[Recebimentos] Comissões geradas: {summary['total_comissoes_geradas']}")
            
            # Log detalhado das estratégias de mapeamento
            for log_entry in log_mapping:
                if log_entry['status'] == 'not_mapped':
                    _debug(f"[AVISO] Recebimento não mapeado - Processo: {log_entry.get('processo')}, Valor: {log_entry.get('valor_recebido')}")
            
            # Atualizar self.estado para compatibilidade
            self.estado = self.state_manager.estado
            
        except Exception as e:
            self._log_validacao('ERRO', f'Erro ao processar recebimentos: {e}')
            self.comissoes_recebimento_df = pd.DataFrame()
'''
    
    # Ler o arquivo
    with open('calculo_comissoes.py', 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    # Encontrar o início da função (linha ~1255)
    inicio = None
    fim = None
    
    for i, line in enumerate(lines):
        if 'def _aplicar_adiantamentos_recebimentos(self):' in line:
            inicio = i
        elif inicio is not None and 'def _executar_reconciliacoes(self):' in line:
            fim = i
            break
    
    if inicio is None or fim is None:
        print(f"[ERRO] Não foi possível encontrar a função. inicio={inicio}, fim={fim}")
        return False
    
    print(f"[INFO] Função encontrada nas linhas {inicio+1} até {fim}")
    print(f"[INFO] Removendo {fim - inicio} linhas, substituindo por {len(novo_conteudo.splitlines())}")
    
    # Substituir
    novas_lines = lines[:inicio] + [novo_conteudo + '\n\n'] + lines[fim:]
    
    # Salvar
    with open('calculo_comissoes.py', 'w', encoding='utf-8') as f:
        f.writelines(novas_lines)
    
    print("[OK] Função _aplicar_adiantamentos_recebimentos substituída!")
    return True

def substituir_executar_reconciliacoes():
    """Substitui a função _executar_reconciliacoes."""
    
    novo_conteudo = '''    def _executar_reconciliacoes(self):
        """
        Executa reconciliações retroativas para processos quitados.
        
        REFATORADO (FASE 4): Usa ReconciliationProcessor para reconciliações.
        
        Processo:
        - Busca processos elegíveis (Quitado + Faturado + Não Reconciliado)
        - Carrega dados históricos do mês de faturamento
        - Recalcula comissões com FC histórico
        - Calcula saldo: comissão_correta - total_adiantado
        - Marca processo como reconciliado
        """
        _info("Iniciando reconciliações de comissões por recebimento...")
        self.reconciliacao_detalhada_list = []
        self.reconciliacao_resumo_list = []
        
        try:
            # Setup do ReconciliationCalculator
            calculator = ReconciliationCalculator(
                analise_comercial_df=self.data.get('ANALISE_COMERCIAL_COMPLETA', pd.DataFrame()),
                fc_calculator_func=self._calcular_fc,  # Reutiliza função existente!
                regras_comissao_getter=self._get_regra_comissao,
                colaboradores_df=self.data.get('COLABORADORES', pd.DataFrame()),
                atribuicoes_df=self.data.get('ATRIBUICOES', pd.DataFrame()),
                recebe_por_recebimento_ids=self.recebe_por_recebimento,
                base_path=self.base_path
            )
            
            # Setup do ReconciliationProcessor
            processor = ReconciliationProcessor(
                state_manager=self.state_manager,
                reconciliation_calculator=calculator
            )
            
            # Processar todas as reconciliações elegíveis
            detalhada_df, resumo_df = processor.process_all_eligible()
            
            # Armazenar para saída
            self.reconciliacao_detalhada_list = detalhada_df.to_dict('records') if not detalhada_df.empty else []
            self.reconciliacao_resumo_list = resumo_df.to_dict('records') if not resumo_df.empty else []
            
            # Log resumo
            if not resumo_df.empty:
                summary = processor.get_processing_summary(resumo_df)
                _info(f"[Reconciliação] Processos: {summary['total_processos']}")
                _info(f"[Reconciliação] Comissão correta total: R$ {summary['comissao_correta_total']:.2f}")
                _info(f"[Reconciliação] Saldo final: R$ {summary['saldo_final_total']:.2f}")
                
                # Log processos que requerem pagamento
                requiring = processor.get_processes_requiring_payment(resumo_df)
                if not requiring.empty:
                    _info(f"[Reconciliação] {len(requiring)} processo(s) requerem pagamento adicional")
                
                # Log processos com pagamento excessivo
                overpaid = processor.get_processes_with_overpayment(resumo_df)
                if not overpaid.empty:
                    _info(f"[Reconciliação] {len(overpaid)} processo(s) com pagamento a maior")
            else:
                _info("[Reconciliação] Nenhum processo elegível para reconciliação")
            
            # Atualizar self.estado para compatibilidade
            self.estado = self.state_manager.estado
            
        except Exception as e:
            self._log_validacao('ERRO', f'Erro ao executar reconciliações: {e}')
            self.reconciliacao_detalhada_list = []
            self.reconciliacao_resumo_list = []
'''
    
    # Ler o arquivo
    with open('calculo_comissoes.py', 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    # Encontrar o início da função
    inicio = None
    fim = None
    
    for i, line in enumerate(lines):
        if 'def _executar_reconciliacoes(self):' in line:
            inicio = i
        elif inicio is not None and i > inicio + 5:  # após encontrar, procurar próxima função
            if line.strip().startswith('def ') and not line.strip().startswith('def _'):
                # função pública - chegamos ao fim
                fim = i
                break
            elif line.strip().startswith('def _') and '_executar_reconciliacoes' not in line:
                # próxima função privada
                fim = i
                break
    
    # Se não achou fim pela próxima função, procurar por linhas em branco seguidas de função
    if inicio and not fim:
        for i in range(inicio + 10, len(lines)):
            if lines[i].strip() == '' and i + 1 < len(lines) and lines[i+1].strip().startswith('def '):
                fim = i + 1
                break
    
    if inicio is None:
        print("[ERRO] Não foi possível encontrar a função _executar_reconciliacoes")
        return False
    
    if fim is None:
        print("[AVISO] Não foi possível determinar o fim exato. Procurando _gerar_reconciliacao_detalhada_processo...")
        for i in range(inicio + 10, len(lines)):
            if 'def _gerar_reconciliacao_detalhada_processo' in lines[i]:
                fim = i
                break
    
    if fim is None:
        print("[ERRO] Não foi possível determinar o fim da função")
        return False
    
    print(f"[INFO] Função encontrada nas linhas {inicio+1} até {fim}")
    print(f"[INFO] Removendo {fim - inicio} linhas, substituindo por {len(novo_conteudo.splitlines())}")
    
    # Substituir
    novas_lines = lines[:inicio] + [novo_conteudo + '\n\n'] + lines[fim:]
    
    # Salvar
    with open('calculo_comissoes.py', 'w', encoding='utf-8') as f:
        f.writelines(novas_lines)
    
    print("[OK] Função _executar_reconciliacoes substituída!")
    return True

def remover_gerar_reconciliacao():
    """Remove a função _gerar_reconciliacao_detalhada_processo."""
    
    # Ler o arquivo
    with open('calculo_comissoes.py', 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    # Encontrar a função
    inicio = None
    fim = None
    
    for i, line in enumerate(lines):
        if 'def _gerar_reconciliacao_detalhada_processo' in line:
            inicio = i
        elif inicio is not None and i > inicio + 10:
            if line.strip().startswith('def ') and '_gerar_reconciliacao' not in line:
                fim = i
                break
    
    if inicio is None:
        print("[INFO] Função _gerar_reconciliacao_detalhada_processo já foi removida ou não encontrada")
        return True
    
    if fim is None:
        print("[AVISO] Fim da função não encontrado. Verificando...")
        # A função deve estar entre _executar_reconciliacoes e outra função
        # Vamos procurar até encontrar a próxima função ou o fim do arquivo
        for i in range(inicio + 100, min(inicio + 600, len(lines))):
            if lines[i].strip().startswith('def '):
                fim = i
                break
        
        if fim is None:
            fim = len(lines)
    
    print(f"[INFO] Removendo função nas linhas {inicio+1} até {fim}")
    print(f"[INFO] Removendo {fim - inicio} linhas")
    
    # Remover
    novas_lines = lines[:inicio] + lines[fim:]
    
    # Salvar
    with open('calculo_comissoes.py', 'w', encoding='utf-8') as f:
        f.writelines(novas_lines)
    
    print("[OK] Função _gerar_reconciliacao_detalhada_processo removida!")
    return True

def main():
    """Executa todas as modificações."""
    print("=" * 80)
    print("APLICANDO MODIFICAÇÕES DA FASE 5")
    print("=" * 80)
    
    if not os.path.exists('calculo_comissoes.py'):
        print("[ERRO] Arquivo calculo_comissoes.py não encontrado!")
        return
    
    # 1. Fazer backup
    backup = fazer_backup()
    
    # 2. Substituir _aplicar_adiantamentos_recebimentos
    print("\n[1/3] Substituindo _aplicar_adiantamentos_recebimentos...")
    if not substituir_aplicar_adiantamentos():
        print("[ERRO] Falha na substituição. Restaurando backup...")
        shutil.copy(backup, 'calculo_comissoes.py')
        return
    
    # 3. Substituir _executar_reconciliacoes
    print("\n[2/3] Substituindo _executar_reconciliacoes...")
    if not substituir_executar_reconciliacoes():
        print("[ERRO] Falha na substituição. Restaurando backup...")
        shutil.copy(backup, 'calculo_comissoes.py')
        return
    
    # 4. Remover _gerar_reconciliacao_detalhada_processo
    print("\n[3/3] Removendo _gerar_reconciliacao_detalhada_processo...")
    if not remover_gerar_reconciliacao():
        print("[AVISO] Não foi possível remover. Continuando...")
    
    print("\n" + "=" * 80)
    print("MODIFICAÇÕES APLICADAS COM SUCESSO!")
    print("=" * 80)
    print(f"\nBackup salvo em: {backup}")
    print("\nPróximos passos:")
    print("1. Revisar as modificações em calculo_comissoes.py")
    print("2. Executar testes: python calculo_comissoes.py")
    print("3. Comparar saída com versão anterior")
    print(f"4. Se houver problemas, restaurar: copy {backup} calculo_comissoes.py")

if __name__ == '__main__':
    main()

