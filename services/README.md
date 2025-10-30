# Serviços de Negócio do Robô de Comissões

Este diretório contém serviços que implementam lógica complexa de negócio para o robô de comissões.

## Módulos

### Serviços de Recebimento

#### `payment_mapper.py`

**Classe: `PaymentMapper`**

Mapeia recebimentos para processos da análise comercial usando múltiplas estratégias progressivas.

**Estratégias de Mapeamento:**
1. **Match Exato:** Processo normalizado igual (ex: 999999 == 999999.0)
2. **Match por Substring:** Processo contém ou está contido (ex: 999999 encontra 999999-A)
3. **Desempate por Valor:** Quando há múltiplos candidatos, escolhe o mais próximo por valor

**Uso:**
```python
from services.payment_mapper import PaymentMapper

mapper = PaymentMapper(analise_comercial_df)

# Mapear um recebimento
row, method = mapper.map_payment(processo=999999, valor_val=1000.0)

if row is not None:
    print(f"Mapeado via {method}")
    context = mapper.get_process_context(row)
    print(f"Linha: {context['linha']}, Grupo: {context['grupo']}")
```

**Métodos Principais:**
- `map_payment(processo, valor, cliente)` - Mapeia recebimento para processo
- `get_process_context(mapped_row)` - Extrai contexto (linha, grupo, tipo, etc)
- `get_mapping_statistics(recebimentos_df)` - Estatísticas de mapeamento

---

#### `payment_commission_calculator.py`

**Classe: `PaymentCommissionCalculator`**

Calcula comissões para colaboradores que recebem por recebimento.

**Fórmula:**
```
comissao = valor_recebido × taxa_rateio × percentual_elegibilidade
FC = 1.0 (sempre, para recebimentos)
```

**Identificação de Colaboradores:**
1. **Gestão:** Por atribuições (contexto: linha, grupo, subgrupo, tipo)
2. **Operacional:** Consultor interno e representante do processo

**Uso:**
```python
from services.payment_commission_calculator import PaymentCommissionCalculator

calculator = PaymentCommissionCalculator(
    regras_comissao_getter=get_regra_func,
    colaboradores_df=colaboradores_df,
    atribuicoes_df=atribuicoes_df,
    recebe_por_recebimento_ids={'João Silva', 'Maria Santos'}
)

# Calcular comissões de um recebimento
comissoes = calculator.calculate_for_payment(
    processo='999999',
    valor_recebido=1000.0,
    process_context={
        'linha': 'Linha A',
        'grupo': 'Grupo 1',
        'consultor_interno': 'João Silva'
    }
)

for com in comissoes:
    print(f"{com['nome_colaborador']}: R$ {com['comissao_calculada']:.2f}")
```

**Métodos Principais:**
- `calculate_for_payment(processo, valor, context)` - Calcula comissões
- `is_payment_receiver(nome)` - Verifica se colaborador recebe por recebimento
- `get_payment_receivers_count()` - Quantidade de colaboradores

---

#### `payment_processor.py`

**Classe: `PaymentProcessor`**

Orquestra o fluxo completo de processamento de recebimentos.

**Fluxo Completo:**
1. Mapear recebimento → processo
2. Extrair contexto do processo
3. Calcular comissões
4. Atualizar estado (opcional)
5. Retornar comissões + logs

**Uso:**
```python
from services.payment_processor import PaymentProcessor
from models.process_state import ProcessStateManager

# Setup
state_manager = ProcessStateManager()
state_manager.load_from_file('Estado_Processos_Recebimento.xlsx')

processor = PaymentProcessor(
    recebimentos_df=recebimentos_df,
    analise_comercial_df=analise_df,
    commission_calculator=calculator,
    state_manager=state_manager
)

# Processar todos os recebimentos
comissoes_df, log_map = processor.process_all_payments()

# Resumo
summary = processor.get_processing_summary(log_map)
print(f"Mapeados: {summary['mapeados']}/{summary['total_recebimentos']}")
print(f"Taxa: {summary['taxa_mapeamento']:.1f}%")
print(f"Comissões geradas: {summary['total_comissoes_geradas']}")

# Recebimentos não mapeados (para análise)
unmapped = processor.get_unmapped_payments(log_map)
for um in unmapped:
    print(f"Processo {um['processo']}: {um['status']}")

# Salvar estado atualizado
state_manager.save_to_file()
```

**Métodos Principais:**
- `process_all_payments()` - Processa todos os recebimentos
- `get_processing_summary(log)` - Resumo estatístico
- `get_unmapped_payments(log)` - Recebimentos não mapeados

---

## Arquitetura

```
PaymentProcessor (orquestrador)
    ├── PaymentMapper (mapeamento)
    │   └── ColumnFinder (utils)
    ├── PaymentCommissionCalculator (cálculo)
    │   └── Normalization (utils)
    └── ProcessStateManager (estado)
        └── Normalization (utils)
```

## Comparação: Antes vs Depois

### Antes da Refatoração

**Função:** `_aplicar_adiantamentos_recebimentos()`
- **Linhas:** ~540 linhas
- **Responsabilidades:** 
  - Normalização
  - Mapeamento
  - Identificação de colaboradores
  - Cálculo de comissões
  - Atualização de estado
  - Logging
- **Funções aninhadas:** 3 (`_normalize_proc`, `_find_column`, `_map_recebimento`)
- **Testabilidade:** Difícil (função monolítica)
- **Duplicação:** Normalização reimplementada

### Depois da Refatoração

**Serviços:** 3 módulos independentes
- **Linhas médias:** ~50-80 linhas por classe
- **Responsabilidades:** Cada classe faz uma coisa
  - `PaymentMapper` → Mapeamento
  - `PaymentCommissionCalculator` → Cálculo
  - `PaymentProcessor` → Orquestração
- **Funções aninhadas:** 0 (métodos privados bem definidos)
- **Testabilidade:** Excelente (8 testes unitários)
- **Duplicação:** Eliminada (usa `utils/`)

## Testes

Execute os testes para verificar funcionamento:

```bash
python tests/test_payment_services.py
```

**Cobertura:**
- ✅ Mapeamento exato
- ✅ Mapeamento por substring
- ✅ Processo não encontrado
- ✅ Extração de contexto
- ✅ Cálculo de comissões
- ✅ Verificação de quem recebe por recebimento
- ✅ Fluxo completo com estado
- ✅ Fluxo sem estado

## Benefícios

✅ **Separação de Responsabilidades:** Cada classe tem um propósito claro  
✅ **Testabilidade:** Componentes podem ser testados isoladamente  
✅ **Manutenibilidade:** Mudanças localizadas, menor risco  
✅ **Reutilização:** Serviços podem ser usados em outros contextos  
✅ **Legibilidade:** Código autodocumentado e claro  
✅ **Performance:** Cache de processos normalizados  
✅ **Debugging:** Logs estruturados de mapeamento

## Próximos Passos

Para usar esses serviços no código principal:

1. Importar os serviços em `calculo_comissoes.py`
2. Substituir `_aplicar_adiantamentos_recebimentos()` por:
```python
def _aplicar_adiantamentos_recebimentos(self):
    # Setup
    calculator = PaymentCommissionCalculator(
        self._get_regra_comissao,
        self.data['COLABORADORES'],
        self.data['ATRIBUICOES'],
        self.recebe_por_recebimento
    )
    
    processor = PaymentProcessor(
        self.data.get('RECEBIMENTOS', pd.DataFrame()),
        self.data['ANALISE_COMERCIAL_COMPLETA'],
        calculator,
        self.state_manager  # já criado na FASE 2
    )
    
    # Processar
    self.comissoes_recebimento_df, log_map = processor.process_all_payments()
    
    # Log
    summary = processor.get_processing_summary(log_map)
    self._log_validacao('INFO', 
        f'Recebimentos processados: {summary["mapeados"]}/{summary["total_recebimentos"]}',
        summary
    )
```

**Resultado:** Função de 540 linhas → 20 linhas! 🎉

---

## Serviços de Reconciliação

### `historical_data_loader.py`

**Classe: `HistoricalDataLoader`**

Carrega dados históricos de um mês/ano específico para recálculo retroativo de comissões.

**Dados Carregados:**
- Faturados do mês
- Conversões do mês
- Faturados YTD (year-to-date)
- Retenção de clientes
- Rentabilidade histórica (da pasta `rentabilidades/`)

**Uso:**
```python
from services.historical_data_loader import HistoricalDataLoader

loader = HistoricalDataLoader(base_path='.')

# Verificar disponibilidade antes de carregar
availability = loader.check_data_availability(mes=7, ano=2025)
if availability['rentabilidade']:
    print("Rentabilidade histórica disponível!")

# Carregar dados
data = loader.load_for_month(mes=7, ano=2025)
print(f"Faturados: {len(data['faturados'])} linhas")
print(f"Conversões: {len(data['conversoes'])} linhas")
print(f"Rentabilidade: {len(data['rentabilidade'])} linhas")

# Listar meses disponíveis
available = loader.get_available_months()
for mes, ano in available:
    print(f"Dados disponíveis para {mes:02d}/{ano}")
```

**Métodos Principais:**
- `load_for_month(mes, ano)` - Carrega todos os dados históricos
- `check_data_availability(mes, ano)` - Verifica disponibilidade
- `get_available_months()` - Lista meses com rentabilidade disponível

---

### `realized_metrics_builder.py`

**Classe: `RealizedMetricsBuilder`**

Constrói séries de métricas realizadas (faturamento, conversão, rentabilidade) para uso no cálculo de FC.

**Séries Construídas:**
1. `faturamento_linha` - Soma de Valor Realizado por Negócio
2. `faturamento_individual` - Soma de Valor Realizado por Consultor
3. `conversao_linha` - Soma de Valor Orçado por Negócio
4. `conversao_individual` - Soma de Valor Orçado por Consultor
5. `rentabilidade` - Rentabilidade por (linha, grupo, subgrupo, tipo) [multi-índice]

**Uso:**
```python
from services.realized_metrics_builder import RealizedMetricsBuilder

builder = RealizedMetricsBuilder()

# Construir séries a partir de DataFrames históricos
series = builder.build_from_dataframes(
    faturados_df=df_faturados_hist,
    conversoes_df=df_conversoes_hist,
    rentabilidade_df=df_rentabilidade_hist
)

# Acessar séries
print(f"Faturamento Linha A: R$ {series['faturamento_linha']['Linha A']:.2f}")
print(f"Faturamento João: R$ {series['faturamento_individual']['João']:.2f}")

# Validar séries construídas
stats = builder.validate_series(series)
for key, stat in stats.items():
    print(f"{key}: {stat['count']} valores, total={stat['total']:.2f}")
```

**Métodos Principais:**
- `build_from_dataframes()` - Constrói todas as séries
- `validate_series()` - Validação e estatísticas

---

### `reconciliation_calculator.py`

**Classe: `ReconciliationCalculator`**

Calcula reconciliação retroativa para processos quitados, recalculando comissões com dados históricos.

**Processo:**
1. Buscar itens do processo na análise comercial
2. Identificar mês/ano de emissão
3. Carregar dados históricos do mês
4. Construir séries de realizados históricos
5. Recalcular comissões item a item com FC histórico

**Fórmula (mesmo do faturamento, mas com FC histórico):**
```
comissao = valor_item × taxa_rateio × PE × FC_HISTORICO
```

**Uso:**
```python
from services.reconciliation_calculator import ReconciliationCalculator

calculator = ReconciliationCalculator(
    analise_comercial_df=analise_df,
    fc_calculator_func=self._calcular_fc,  # função existente
    regras_comissao_getter=self._get_regra_comissao,
    colaboradores_df=colaboradores_df,
    atribuicoes_df=atribuicoes_df,
    recebe_por_recebimento_ids={'João Silva'},
    base_path='.'
)

# Reconciliar um processo
linhas_detalhadas, total = calculator.reconcile_process('999999')

print(f"Comissão correta total: R$ {total:.2f}")
print(f"Linhas detalhadas: {len(linhas_detalhadas)}")

for linha in linhas_detalhadas:
    print(f"{linha['nome_colaborador']}: R$ {linha['comissao_calculada']:.2f}")
```

**Métodos Principais:**
- `reconcile_process(processo_id)` - Reconcilia um processo completo
- `_get_process_items()` - Busca itens na análise
- `_extract_emission_date()` - Extrai data de emissão

---

### `reconciliation_processor.py`

**Classe: `ReconciliationProcessor`**

Orquestra o processamento completo de todas as reconciliações elegíveis.

**Processos Elegíveis:**
- `STATUS_PAGAMENTO == 'Quitado'`
- `STATUS_PROCESSO_ANALISE == 'Faturado'`
- `STATUS_RECONCILIACAO != 'Realizada'`

**Fluxo:**
1. Buscar processos elegíveis do estado
2. Para cada processo: calcular reconciliação
3. Calcular saldo: comissão_correta - total_adiantado
4. Marcar processo como reconciliado
5. Gerar tabelas: detalhada (item a item) e resumo (por processo)

**Uso:**
```python
from services.reconciliation_processor import ReconciliationProcessor
from models.process_state import ProcessStateManager

# Setup
state_manager = ProcessStateManager()
state_manager.load_from_file('Estado_Processos_Recebimento.xlsx')

processor = ReconciliationProcessor(
    state_manager=state_manager,
    reconciliation_calculator=calculator
)

# Processar todos os elegíveis
detalhada_df, resumo_df = processor.process_all_eligible()

# Resumo estatístico
summary = processor.get_processing_summary(resumo_df)
print(f"Processos reconciliados: {summary['total_processos']}")
print(f"Comissão correta total: R$ {summary['comissao_correta_total']:.2f}")
print(f"Saldo final: R$ {summary['saldo_final_total']:.2f}")

# Processos que precisam de pagamento adicional (saldo > 0)
requiring = processor.get_processes_requiring_payment(resumo_df)
print(f"\n{len(requiring)} processos requerem pagamento adicional:")
for _, proc in requiring.iterrows():
    print(f"  {proc['PROCESSO']}: R$ {proc['SALDO_FINAL_RECONCILIACAO']:.2f}")

# Processos com pagamento excessivo (saldo < 0)
overpaid = processor.get_processes_with_overpayment(resumo_df)
print(f"\n{len(overpaid)} processos com pagamento a maior:")
for _, proc in overpaid.iterrows():
    print(f"  {proc['PROCESSO']}: R$ {proc['SALDO_FINAL_RECONCILIACAO']:.2f}")

# Validar consistência
validation = processor.validate_reconciliation_data(detalhada_df, resumo_df)
if validation['validacao_ok']:
    print("\n✅ Validação OK! Dados consistentes.")
else:
    print("\n⚠️ Validação falhou:")
    print(f"  Somas consistentes: {validation['somas_consistentes']}")
    print(f"  Todos processos têm detalhes: {validation['todos_processos_tem_detalhes']}")
    print(f"  Sem valores inválidos: {validation['sem_valores_invalidos']}")

# Salvar estado atualizado
state_manager.save_to_file()
```

**Métodos Principais:**
- `process_all_eligible()` - Processa todas as reconciliações elegíveis
- `get_processing_summary(resumo_df)` - Estatísticas do processamento
- `get_processes_requiring_payment(resumo_df)` - Processos com saldo > 0
- `get_processes_with_overpayment(resumo_df)` - Processos com saldo < 0
- `validate_reconciliation_data()` - Validação de consistência

---

## Arquitetura Completa

```
PaymentProcessor (recebimentos)
    ├── PaymentMapper
    ├── PaymentCommissionCalculator
    └── ProcessStateManager

ReconciliationProcessor (reconciliações)
    ├── ReconciliationCalculator
    │   ├── HistoricalDataLoader
    │   ├── RealizedMetricsBuilder
    │   └── FC Calculator (reutilizado do fluxo principal)
    └── ProcessStateManager
```

## Comparação: Reconciliações

### Antes da Refatoração

**Função:** `_gerar_reconciliacao_detalhada_processo()`
- **Linhas:** ~487 linhas
- **Responsabilidades:** 
  - Carregamento de dados históricos
  - Construção de séries de realizados
  - Mapeamento de colunas
  - Cálculo de reconciliação item a item
  - Geração de resumo
- **Funções aninhadas:** 5 (`_match_column`, `_safe_float`, `_build_group_series`, etc)
- **Testabilidade:** Difícil (função monolítica com dependências externas)
- **Duplicação:** Lógica de séries reimplementada

### Depois da Refatoração

**Serviços:** 4 módulos independentes
- **Linhas médias:** ~70-100 linhas por classe
- **Responsabilidades:** Cada classe faz uma coisa
  - `HistoricalDataLoader` → Carregamento
  - `RealizedMetricsBuilder` → Construção de séries
  - `ReconciliationCalculator` → Cálculo
  - `ReconciliationProcessor` → Orquestração
- **Funções aninhadas:** 0 (métodos privados bem definidos)
- **Testabilidade:** Excelente (10 testes unitários)
- **Duplicação:** Eliminada (usa `utils/` e reutiliza FC do fluxo principal)

## Testes Completos

Execute todos os testes:

```bash
# Testes de recebimento
python tests/test_payment_services.py

# Testes de reconciliação
python tests/test_reconciliation_services.py
```

**Cobertura Total:**
- ✅ 8 testes de recebimento
- ✅ 10 testes de reconciliação
- ✅ **18 testes unitários** no total

## Métricas de Melhoria

### Redução de Complexidade

**McCabe Complexity (complexidade ciclomática):**

| Componente | Antes | Depois | Redução |
|-----------|-------|--------|---------|
| Recebimentos | ~45 | ~5-8 | **89%** |
| Reconciliações | ~42 | ~6-10 | **85%** |

### Linhas de Código

| Componente | Antes | Depois | Redução |
|-----------|-------|--------|---------|
| Recebimentos | 540 linhas | 3 módulos × ~60 linhas | **67%** |
| Reconciliações | 487 linhas | 4 módulos × ~80 linhas | **34%** |

**Total:** 1027 linhas → 500 linhas (~51% de redução)

## Benefícios Gerais

✅ **Separação de Responsabilidades:** Cada classe tem um propósito claro  
✅ **Testabilidade:** Componentes podem ser testados isoladamente  
✅ **Manutenibilidade:** Mudanças localizadas, menor risco  
✅ **Reutilização:** Serviços podem ser usados em outros contextos  
✅ **Legibilidade:** Código autodocumentado e claro  
✅ **Performance:** Cache de processos e séries  
✅ **Debugging:** Logs estruturados em cada etapa  
✅ **Escalabilidade:** Fácil adicionar novas estratégias/cálculos

