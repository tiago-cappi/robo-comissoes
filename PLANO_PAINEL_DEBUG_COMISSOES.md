# Plano de Execução: Painel de Depuração Completo para Comissões por Recebimento e Reconciliações

## Objetivo
Criar um painel de depuração completo na aba `ESTADO` que mostre passo a passo como cada processo foi calculado, quais dados foram usados e de qual arquivo/coluna foram retirados.

---

## FASE 1: Backend - Estrutura de Dados de Debug

### Etapa 1.1: Expandir Colunas do Estado
**Arquivo:** `models/process_state.py`
**Tarefa:** Adicionar novas colunas ao `ESTADO_COLUMNS` para armazenar logs de debug
- [ ] Adicionar `LOG_EVENTOS` (TEXT) - Log cronológico de eventos
- [ ] Adicionar `FONTE_PAGAMENTOS` (TEXT) - Nome do arquivo fonte
- [ ] Adicionar `PAGAMENTOS_PROCESSADOS` (TEXT/JSON) - Lista de pagamentos processados
- [ ] Adicionar `DETALHES_CALCULO_METRICAS` (TEXT/JSON) - Detalhes do cálculo TCMP/FCMP
- [ ] Adicionar `DETALHES_CALCULO_RECONCILIACAO` (TEXT/JSON) - Detalhes do saldo de reconciliação
- [ ] Atualizar `_normalize_estado()` para tratar essas novas colunas

**Estimativa:** 15 minutos
**Dependências:** Nenhuma

---

### Etapa 1.2: Criar Helper para Log de Eventos
**Arquivo:** `calculo_comissoes.py` (novo método na classe)
**Tarefa:** Criar método auxiliar para construir logs estruturados
- [ ] Criar método `_adicionar_log_evento(processo, evento, detalhes=None)`
- [ ] Formato: `[YYYY-MM-DD HH:MM] Evento: detalhes`
- [ ] Acumular logs em lista temporária por processo
- [ ] Salvar no estado ao final do processamento

**Estimativa:** 20 minutos
**Dependências:** Etapa 1.1

---

### Etapa 1.3: Logar Pagamentos Processados
**Arquivo:** `calculo_comissoes.py` - método `_calcular_comissoes_recebimento_nova_logica`
**Tarefa:** Capturar e logar cada pagamento identificado
- [ ] Ao processar cada linha do `FinancialPaymentsLoader`:
  - Capturar: tipo, documento original, valor, data, processo identificado
  - Adicionar log: `"Pagamento 'Tipo' (Documento) de R$X processado"`
  - Acumular em lista `PAGAMENTOS_PROCESSADOS` (JSON)
- [ ] Salvar `FONTE_PAGAMENTOS = "Análise Financeira.xlsx"` no estado
- [ ] Chamar `_adicionar_log_evento()` para cada pagamento

**Estimativa:** 30 minutos
**Dependências:** Etapa 1.2

---

### Etapa 1.4: Logar Detalhes do Cálculo de Métricas (TCMP/FCMP)
**Arquivo:** `calculo_comissoes.py` - método `_reconciliar_e_calcular_metricas_do_mes`
**Tarefa:** Capturar detalhes do cálculo de TCMP/FCMP por processo
- [ ] Ao calcular métricas para um processo:
  - Capturar: colaboradores processados, TCMP/FCMP de cada um
  - Capturar: itens usados no cálculo (código produto, valor realizado)
  - Capturar: valor total dos itens
  - Montar JSON `DETALHES_CALCULO_METRICAS`:
    ```json
    {
      "status": "Sucesso",
      "colaboradores": {"Nome": {"tcmp": 0.025, "fcmp": 0.95}},
      "itens_usados": ["PROD-A", "PROD-B"],
      "valor_total_itens": 150000
    }
    ```
  - Adicionar log: `"Métricas TCMP/FCMP calculadas para X colaboradores"`

**Estimativa:** 40 minutos
**Dependências:** Etapa 1.2

---

### Etapa 1.5: Logar Detalhes do Cálculo de Reconciliação
**Arquivo:** `calculo_comissoes.py` - método `_reconciliar_e_calcular_metricas_do_mes`
**Tarefa:** Capturar detalhes do cálculo do saldo de reconciliação
- [ ] Ao calcular saldo para um processo com adiantamentos:
  - Capturar: `total_adiantado_comissao`
  - Capturar: `fcmp_medio_ponderado` (ou FCMP por colaborador)
  - Capturar: `saldo_calculado`
  - Montar JSON `DETALHES_CALCULO_RECONCILIACAO`:
    ```json
    {
      "status": "Aplicado",
      "total_adiantado_comissao": 500.00,
      "fcmp_medio_ponderado": 0.95,
      "saldo_calculado": -25.00,
      "formula": "Total_Adiantado × (FCMP - 1)"
    }
    ```
  - Adicionar log: `"Saldo de reconciliação de R$X calculado"`

**Estimativa:** 30 minutos
**Dependências:** Etapa 1.2, 1.4

---

### Etapa 1.6: Criar Aba DEBUG_PAGAMENTOS_FINANCEIRO
**Arquivo:** `calculo_comissoes.py` - método `_gerar_saida_impl`
**Tarefa:** Gerar nova aba com dados normalizados do FinancialPaymentsLoader
- [ ] Após processar pagamentos, salvar snapshot do DataFrame normalizado
- [ ] Criar aba `DEBUG_PAGAMENTOS_FINANCEIRO` no Excel de saída
- [ ] Incluir todas as colunas normalizadas:
  - `DOCUMENTO_ORIGINAL`, `VALOR_PAGO`, `DATA_PAGAMENTO`, `ID_CLIENTE`
  - `TIPO_PAGAMENTO`, `PROCESSO`, `DOCUMENTO_NORMALIZADO`
- [ ] Adicionar comentário explicativo na primeira linha (se possível)

**Estimativa:** 25 minutos
**Dependências:** Nenhuma (independente)

---

## FASE 2: Backend - Persistência dos Logs no Estado

### Etapa 2.1: Salvar Logs no Estado Durante Processamento
**Arquivo:** `calculo_comissoes.py` - métodos de cálculo
**Tarefa:** Integrar salvamento de logs no `ProcessStateManager`
- [ ] Modificar `_calcular_comissoes_recebimento_nova_logica`:
  - Após processar todos os pagamentos de um processo, salvar logs acumulados
  - Chamar método do `state_manager` para atualizar colunas de debug
- [ ] Modificar `_reconciliar_e_calcular_metricas_do_mes`:
  - Após calcular métricas/reconciliação, salvar detalhes no estado
- [ ] Garantir que logs sejam salvos mesmo se houver erro parcial

**Estimativa:** 35 minutos
**Dependências:** Etapas 1.1, 1.2, 1.3, 1.4, 1.5

---

### Etapa 2.2: Criar Método no ProcessStateManager para Atualizar Debug
**Arquivo:** `models/process_state.py`
**Tarefa:** Adicionar método para atualizar colunas de debug
- [ ] Criar método `update_process_debug(processo, **kwargs)`:
  - Aceitar: `log_eventos`, `fonte_pagamentos`, `pagamentos_processados`, etc.
  - Atualizar ou criar linha no estado com essas informações
  - Garantir que não sobrescreva dados existentes (append em logs)

**Estimativa:** 25 minutos
**Dependências:** Etapa 1.1

---

## FASE 3: Frontend - Visualização do Painel de Depuração

### Etapa 3.1: Expandir Colunas da Aba ESTADO no Frontend
**Arquivo:** `frontend/src/pages/ResultadosPage.js`
**Tarefa:** Adicionar renderização das novas colunas de debug
- [ ] Identificar onde as colunas da aba ESTADO são definidas
- [ ] Adicionar colunas:
  - `LOG_EVENTOS` (renderizar como texto com quebras de linha)
  - `FONTE_PAGAMENTOS` (texto simples)
  - `PAGAMENTOS_PROCESSADOS` (botão "Ver Detalhes" → modal JSON)
  - `DETALHES_CALCULO_METRICAS` (botão "Ver Detalhes" → modal JSON)
  - `DETALHES_CALCULO_RECONCILIACAO` (botão "Ver Detalhes" → modal JSON)
- [ ] Criar renderizadores customizados para colunas JSON

**Estimativa:** 45 minutos
**Dependências:** Fase 1 completa

---

### Etapa 3.2: Criar Modal para Visualizar JSON de Debug
**Arquivo:** `frontend/src/components/DebugJsonModal.js` (NOVO)
**Tarefa:** Criar componente modal reutilizável para exibir JSON formatado
- [ ] Criar componente que recebe título e JSON
- [ ] Formatar JSON com syntax highlighting (usar biblioteca ou CSS)
- [ ] Adicionar botão de copiar JSON
- [ ] Layout limpo e legível

**Estimativa:** 30 minutos
**Dependências:** Nenhuma (pode ser feito em paralelo)

---

### Etapa 3.3: Integrar Modal de Debug na Aba ESTADO
**Arquivo:** `frontend/src/pages/ResultadosPage.js`
**Tarefa:** Conectar botões "Ver Detalhes" ao modal
- [ ] Adicionar handlers de clique nos botões de debug
- [ ] Abrir `DebugJsonModal` com dados correspondentes
- [ ] Testar com dados reais

**Estimativa:** 25 minutos
**Dependências:** Etapa 3.1, 3.2

---

### Etapa 3.4: Melhorar Modal de Recebimento com Fórmulas Detalhadas
**Arquivo:** `frontend/src/components/RecebimentoModal.js`
**Tarefa:** Expandir modal para mostrar cálculo passo a passo
- [ ] Identificar se é Adiantamento ou Parcela
- [ ] **Para Adiantamento:**
  - Mostrar: `Valor × TCMP (FC=1.0)`
  - Exibir TCMP temporária se disponível
  - Explicar: "Taxa máxima da linha, pois FCMP ainda não está disponível"
- [ ] **Para Parcela:**
  - Mostrar: `Valor × TCMP × FCMP`
  - Destacar FCMP aplicado
  - Explicar: "TCMP e FCMP calculados e armazenados no mês de faturamento"
- [ ] Adicionar seção "Fonte dos Dados" mostrando arquivo/coluna

**Estimativa:** 40 minutos
**Dependências:** Nenhuma (pode ser feito em paralelo)

---

### Etapa 3.5: Atualizar Modal de Reconciliação com Detalhes
**Arquivo:** `frontend/src/components/ReconProcessoModal.js`
**Tarefa:** Mostrar componentes do cálculo do saldo
- [ ] Exibir fórmula: `Saldo = Total_Adiantado × (FCMP - 1)`
- [ ] Mostrar breakdown:
  - Total de comissão adiantada
  - FCMP médio ponderado (ou por colaborador)
  - Cálculo passo a passo
- [ ] Adicionar seção "Fonte dos Dados"

**Estimativa:** 35 minutos
**Dependências:** Nenhuma (pode ser feito em paralelo)

---

### Etapa 3.6: Adicionar Tags Visuais para Tipo de Pagamento
**Arquivo:** `frontend/src/pages/ResultadosPage.js`
**Tarefa:** Adicionar badges coloridos na aba COMISSOES_RECEBIMENTO
- [ ] Identificar coluna `TIPO_PAGAMENTO` ou similar
- [ ] Renderizar Tag:
  - `[ Adiantamento ]` (Azul) para "Antecipação"
  - `[ Pagamento Regular ]` (Verde) para "Pagamento Regular"
- [ ] Aplicar na linha mestre (processo) e na linha de item

**Estimativa:** 20 minutos
**Dependências:** Nenhuma (pode ser feito em paralelo)

---

## FASE 4: Testes e Validação

### Etapa 4.1: Teste End-to-End com Dados Reais
**Tarefa:** Executar cálculo completo e verificar logs
- [ ] Rodar cálculo de comissões
- [ ] Verificar se aba ESTADO contém todas as novas colunas
- [ ] Verificar se logs estão sendo preenchidos corretamente
- [ ] Verificar se JSONs estão bem formatados
- [ ] Verificar se frontend exibe tudo corretamente

**Estimativa:** 30 minutos
**Dependências:** Todas as fases anteriores

---

### Etapa 4.2: Validar Dados de Debug com Casos Conhecidos
**Tarefa:** Comparar logs com cálculos manuais
- [ ] Selecionar 2-3 processos com adiantamentos conhecidos
- [ ] Verificar se logs mostram os pagamentos corretos
- [ ] Verificar se métricas calculadas batem com expectativa
- [ ] Verificar se saldo de reconciliação está correto

**Estimativa:** 45 minutos
**Dependências:** Etapa 4.1

---

### Etapa 4.3: Testar Aba DEBUG_PAGAMENTOS_FINANCEIRO
**Tarefa:** Validar dados normalizados
- [ ] Abrir Excel gerado e verificar aba `DEBUG_PAGAMENTOS_FINANCEIRO`
- [ ] Comparar com arquivo original `Análise Financeira.xlsx`
- [ ] Verificar se classificação "COT" vs "Pagamento Regular" está correta
- [ ] Verificar se extração de Processo/NF está correta

**Estimativa:** 25 minutos
**Dependências:** Etapa 1.6

---

## Resumo de Estimativas

- **Fase 1 (Backend - Estrutura):** ~2h 30min
- **Fase 2 (Backend - Persistência):** ~1h
- **Fase 3 (Frontend - Visualização):** ~3h 15min
- **Fase 4 (Testes):** ~1h 40min

**Total Estimado:** ~8h 25min

---

## Ordem de Execução Recomendada

1. **Fase 1 completa** (estrutura de dados)
2. **Fase 2 completa** (persistência)
3. **Fase 3.2** (modal JSON - pode ser feito em paralelo)
4. **Fase 3.1, 3.3** (integração frontend)
5. **Fase 3.4, 3.5, 3.6** (melhorias visuais - podem ser feitas em paralelo)
6. **Fase 4** (testes)

---

## Notas Importantes

- **Não alterar lógica de cálculo:** Apenas adicionar logging/visualização
- **Tolerância a erros:** Se algum log falhar, não deve quebrar o cálculo
- **Performance:** Logs devem ser eficientes (evitar loops desnecessários)
- **Compatibilidade:** Garantir que código funcione mesmo se novas colunas estiverem vazias

---

## Próximos Passos

Após aprovação deste plano, começar pela **Etapa 1.1** e seguir sequencialmente.

