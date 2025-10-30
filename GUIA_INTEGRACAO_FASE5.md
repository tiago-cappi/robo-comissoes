# Guia de Integração - FASE 5

Este guia detalha as mudanças necessárias para integrar os novos serviços no `calculo_comissoes.py`.

## 📋 Visão Geral das Mudanças

### 1. Imports Novos (início do arquivo)

```python
# Adicionar após os imports existentes
from models.process_state import ProcessStateManager
from services.payment_mapper import PaymentMapper
from services.payment_commission_calculator import PaymentCommissionCalculator
from services.payment_processor import PaymentProcessor
from services.reconciliation_calculator import ReconciliationCalculator
from services.reconciliation_processor import ReconciliationProcessor
```

### 2. Mudanças no `__init__` da Classe

**Antes:**
```python
def __init__(self):
    self.data = {}
    self.params = {}
    self.validation_log = []
    # ... outros atributos ...
    self.base_path = os.getcwd()
```

**Depois:**
```python
def __init__(self):
    self.data = {}
    self.params = {}
    self.validation_log = []
    # ... outros atributos ...
    self.base_path = os.getcwd()
    
    # NOVO: ProcessStateManager (substituir self.estado)
    self.state_manager = ProcessStateManager(log_callback=self._log_validacao)
```

### 3. Substituir `_carregar_estado()` 

**Localização:** Linha ~1159, chamado em `executar()` linha ~3494

**Antes (87 linhas):**
```python
def _carregar_estado(self):
    """Carrega ou inicializa a planilha de estado dos processos."""
    # ... 87 linhas de código ...
    self.estado = df
```

**Depois (3 linhas):**
```python
def _carregar_estado(self):
    """Carrega ou inicializa a planilha de estado dos processos."""
    filepath = os.path.join(self.base_path, 'Estado_Processos_Recebimento.xlsx')
    self.state_manager.load_from_file(filepath)
    self.estado = self.state_manager.estado  # Para compatibilidade com código existente
```

### 4. Substituir `_salvar_estado()`

**Localização:** Linha ~1190, chamado em `executar()` linha ~3502

**Antes (13 linhas):**
```python
def _salvar_estado(self):
    """Salva o DataFrame de estado em Excel."""
    # ... 13 linhas de código ...
```

**Depois (3 linhas):**
```python
def _salvar_estado(self):
    """Salva o DataFrame de estado em Excel."""
    filepath = os.path.join(self.base_path, 'Estado_Processos_Recebimento.xlsx')
    self.state_manager.save_to_file(filepath)
```

### 5. Substituir `_aplicar_adiantamentos_recebimentos()`

**Localização:** Linha ~1257, chamado em `executar()` linha ~3495

**Antes (540 linhas!):**
```python
def _aplicar_adiantamentos_recebimentos(self):
    """Calcula e aplica adiantamentos de comissão baseados nos recebimentos do mês."""
    # ... 540 linhas de código spaghetti ...
```

**Depois (~40 linhas):**
```python
def _aplicar_adiantamentos_recebimentos(self):
    """Calcula e aplica adiantamentos de comissão baseados nos recebimentos do mês."""
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
        
        # Atualizar self.estado para compatibilidade
        self.estado = self.state_manager.estado
        
    except Exception as e:
        self._log_validacao('ERRO', f'Erro ao processar recebimentos: {e}')
        self.comissoes_recebimento_df = pd.DataFrame()
```

### 6. Substituir `_executar_reconciliacoes()`

**Localização:** Linha ~1798, chamado em `executar()` linha ~3497

**Antes (~74 linhas + chama _gerar_reconciliacao_detalhada_processo de 487 linhas):**
```python
def _executar_reconciliacoes(self):
    """Executa reconciliações retroativas para processos quitados."""
    # ... 74 linhas ...
    # chama _gerar_reconciliacao_detalhada_processo (487 linhas)
```

**Depois (~35 linhas):**
```python
def _executar_reconciliacoes(self):
    """Executa reconciliações retroativas para processos quitados."""
    _debug("[DEBUG] Executando reconciliações usando ReconciliationProcessor...")
    
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
        
        # Atualizar self.estado para compatibilidade
        self.estado = self.state_manager.estado
        
    except Exception as e:
        self._log_validacao('ERRO', f'Erro ao executar reconciliações: {e}')
        self.reconciliacao_detalhada_list = []
        self.reconciliacao_resumo_list = []
```

### 7. Remover Funções Obsoletas

Estas funções podem ser **removidas** após a integração:

- ❌ `_gerar_reconciliacao_detalhada_processo()` (~487 linhas) - Substituída por ReconciliationCalculator
- ⚠️ **NÃO remover** `_aplicar_adiantamentos_recebimentos()` e `_executar_reconciliacoes()` - apenas substituir o conteúdo

### 8. Compatibilidade

Para garantir que o resto do código continue funcionando:

- ✅ Manter `self.estado` atualizado após operações: `self.estado = self.state_manager.estado`
- ✅ `_get_regra_comissao()` continua sendo usado (reutilizado pelos serviços)
- ✅ `_calcular_fc()` continua sendo usado (reutilizado pelo ReconciliationCalculator)
- ✅ `self.recebe_por_recebimento` continua sendo usado

## 📊 Resumo de Redução

| Componente | Antes | Depois | Redução |
|-----------|-------|--------|---------|
| `_carregar_estado()` | 87 linhas | 3 linhas | **97%** |
| `_salvar_estado()` | 13 linhas | 3 linhas | **77%** |
| `_aplicar_adiantamentos_recebimentos()` | 540 linhas | 40 linhas | **93%** |
| `_executar_reconciliacoes()` | 74 linhas | 35 linhas | **53%** |
| `_gerar_reconciliacao_detalhada_processo()` | 487 linhas | 0 linhas | **100%** |
| **TOTAL** | **1201 linhas** | **81 linhas** | **93%** |

**Resultado:** Redução de ~1120 linhas no arquivo principal! 🚀

## ✅ Checklist de Integração

- [ ] 1. Adicionar imports dos novos serviços
- [ ] 2. Adicionar `self.state_manager` no `__init__`
- [ ] 3. Substituir `_carregar_estado()`
- [ ] 4. Substituir `_salvar_estado()`
- [ ] 5. Substituir `_aplicar_adiantamentos_recebimentos()`
- [ ] 6. Substituir `_executar_reconciliacoes()`
- [ ] 7. Remover `_gerar_reconciliacao_detalhada_processo()`
- [ ] 8. Testar execução completa
- [ ] 9. Verificar que saída Excel é idêntica
- [ ] 10. Validar logs e mensagens

## 🔄 Estratégia de Migração Segura

1. **Backup:** Fazer cópia de `calculo_comissoes.py` original
2. **Integração:** Aplicar mudanças uma por vez
3. **Teste:** Executar após cada mudança
4. **Validação:** Comparar saída com versão anterior
5. **Rollback:** Se houver problema, voltar para backup

## 🎯 Próximos Passos

Após a integração, o arquivo `calculo_comissoes.py` terá:
- ✅ ~1200 linhas a menos
- ✅ Funções curtas e focadas
- ✅ Separação clara de responsabilidades
- ✅ Código testado (39 testes unitários nos serviços)
- ✅ Fácil manutenção e extensão

---

**Criado em:** 30/10/2025  
**Status:** Pronto para implementação

