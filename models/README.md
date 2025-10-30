# Modelos de Dados do Robô de Comissões

Este diretório contém classes que gerenciam estruturas de dados complexas e estados persistentes.

## Módulos

### `process_state.py`

Gerenciamento centralizado do estado dos processos (ESTADO).

#### Classe: `ProcessStateManager`

Gerencia o DataFrame de estado que rastreia:
- Valores totais dos processos
- Total pago acumulado (recebimentos)
- Total de comissões adiantadas
- Status de pagamento e reconciliação

**Esquema do Estado:**
```
PROCESSO                   | ID do processo (string normalizada)
VALOR_TOTAL_PROCESSO       | Valor total do processo (float)
TOTAL_PAGO_ACUMULADO       | Total recebido acumulado (float)
TOTAL_ADIANTADO_COMISSAO   | Total de comissões adiantadas (float)
STATUS_PAGAMENTO           | Status do pagamento (ex: "Quitado", "Em Aberto")
STATUS_RECONCILIACAO       | Status da reconciliação ("Nao Realizada", "Realizada")
STATUS_PROCESSO_ANALISE    | Status na análise (ex: "Faturado")
ULTIMA_ATUALIZACAO         | Timestamp da última atualização (ISO)
```

#### Uso Básico

```python
from models.process_state import ProcessStateManager

# Criar manager
manager = ProcessStateManager()

# Carregar estado existente
manager.load_from_file('Estado_Processos_Recebimento.xlsx')

# Registrar recebimento
manager.update_payment_received(
    processo_id=999999,
    valor_recebido=1000.0,
    valor_total_processo=5000.0,
    status_pagamento='Em Aberto'
)

# Registrar comissão adiantada
manager.update_commission_advanced(999999, 250.0)

# Atualizar status
manager.update_process_status(
    999999,
    status_processo_analise='Faturado',
    status_pagamento='Quitado'
)

# Buscar processos elegíveis para reconciliação
eligible = manager.get_eligible_for_reconciliation()

# Marcar reconciliação concluída
manager.mark_reconciliation_done(999999)

# Salvar estado
manager.save_to_file()

# Obter resumo estatístico
summary = manager.get_process_summary()
print(f"Total de processos: {summary['total_processos']}")
print(f"Total pago: R$ {summary['total_pago']:,.2f}")
```

#### Métodos Principais

**Consulta:**
- `get_process_state(processo_id)` - Retorna dict com estado do processo
- `process_exists(processo_id)` - Verifica se processo existe
- `get_eligible_for_reconciliation()` - Processos elegíveis (Quitado + Faturado)
- `get_process_summary()` - Estatísticas gerais
- `get_dataframe()` - Retorna cópia do DataFrame

**Atualização:**
- `update_payment_received()` - Registra recebimento (cria ou incrementa)
- `update_commission_advanced()` - Incrementa comissão adiantada
- `update_process_status()` - Atualiza status de análise/pagamento
- `mark_reconciliation_done()` - Marca reconciliação como realizada

**Persistência:**
- `load_from_file(filepath)` - Carrega de Excel
- `save_to_file(filepath)` - Salva em Excel

#### Regras de Negócio

1. **Criação de Processo:**
   - Processo é criado automaticamente na primeira atualização
   - STATUS_RECONCILIACAO inicia como "Nao Realizada"

2. **Acumulação:**
   - `TOTAL_PAGO_ACUMULADO` é **incrementado** a cada recebimento
   - `TOTAL_ADIANTADO_COMISSAO` é **incrementado** a cada adiantamento
   - Permite múltiplos recebimentos/adiantamentos por processo

3. **Elegibilidade para Reconciliação:**
   - STATUS_PAGAMENTO contém "QUITADO"
   - STATUS_PROCESSO_ANALISE == "FATURADO"
   - STATUS_RECONCILIACAO != "REALIZADA" ou "CONCLUIDA"

4. **Normalização Automática:**
   - IDs de processos são normalizados (999999.0 → "999999")
   - Status são normalizados para comparação (case-insensitive, sem acentos)
   - Tipos numéricos são convertidos e validados

#### Testes

Execute os testes para verificar funcionamento:

```bash
python tests/test_process_state.py
```

## Benefícios

✅ **Interface clara:** Métodos bem definidos e documentados  
✅ **Validação automática:** Tipos e valores normalizados  
✅ **Consistência:** Regras de negócio centralizadas  
✅ **Testabilidade:** Fácil testar isoladamente  
✅ **Manutenibilidade:** Mudanças em um só lugar  
✅ **Rastreabilidade:** Timestamps automáticos de atualização

