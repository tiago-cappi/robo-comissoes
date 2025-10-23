**Visão Geral**
- Robô que calcula comissões por faturamento, por recebimento e reconciliações retroativas por processo, gerando um Excel consolidado com planilhas de cálculo, resumo e depuração, além de um PDF opcional de detalhamento.
- Fluxo de alto nível: carrega dados → normaliza/parametriza → calcula “realizados” → calcula comissões de faturamento (item a item) → aplica adiantamentos por recebimento → executa reconciliações retroativas (quando quitado e faturado) → gera saídas (Excel + PDF + logs).

**Arquivos De Entrada**
- `Regras_Comissoes.xlsx` (obrigatório):
  - `PARAMS`: parâmetros de execução (ex.: `cap_fc_max`, `cap_atingimento_max`, flags de debug, aliases etc.).
  - `CONFIG_COMISSAO`: regras por contexto (linha, grupo, subgrupo, tipo_mercadoria, cargo) com colunas chave como `taxa_rateio_maximo_pct`, `fatia_cargo_pct`.
  - `PESOS_METAS`: pesos por cargo para compor o FC; colunas padrão: `faturamento_linha`, `conversao_linha`, `faturamento_individual`, `conversao_individual`, `rentabilidade`. Pode incluir `retencao_clientes`, `meta_fornecedor_1`, `meta_fornecedor_2`.
  - `METAS_APLICACAO`: metas por (linha, tipo_mercadoria) para componentes “linha”.
  - `METAS_INDIVIDUAIS`: metas por colaborador para componentes “individual”.
  - `META_RENTABILIDADE`: metas de rentabilidade por (linha, grupo, subgrupo, tipo_mercadoria).
  - `METAS_FORNECEDORES`: metas por fornecedor (fabricante) e linha, com moeda; usado para componentes de fornecedor.
  - `COLABORADORES`: colaboradores, cargos e atributos (inclui `TIPO_COMISSAO` quando aplicável);
  - `CARGOS`: metadados dos cargos (inclui `TIPO_COMISSAO` ou heurística pelo nome).
  - `ALIASES`: mapeia nomes alternativos de colaboradores para formas canônicas (entidade=colaborador).
  - `CROSS_SELLING` (opcional): taxa padrão (%) para consultor externo sem atribuição na linha.
- `Faturados*.xlsx|csv` (opcional): itens faturados (precisa de colunas como `Processo`, `Cód(igo) Produto`, `Descrição Produto`, `Negócio`, `Grupo`, `Subgrupo`, `Tipo de Mercadoria`, `Valor Realizado`, `Consultor Interno`, `Representante-pedido`).
- `Conversões*.xlsx|csv` (opcional): orçamentos, usados nos componentes de conversão.
- `Rentabilidade_Realizada_*.xlsx` (obrigatório para rentabilidade): rentabilidade efetiva por (linha, Grupo, Subgrupo, Tipo de Mercadoria). Alternativamente, arquivos históricos em `rentabilidades/rentabilidade_{MM}_{AAAA}_agrupada.(xlsx|csv)` para reconciliação.
- `Faturados_YTD_*.xlsx` (opcional): base para metas de fornecedor YTD por moeda/fabricante.
- `Recebimentos_do_Mes.xlsx` (opcional): recebimentos com colunas `PROCESSO`, `VALOR_RECEBIDO`, `DATA_RECEBIMENTO`, `ID_CLIENTE`.
- `Status_Pagamentos_Processos.xlsx` (opcional): status por processo; colunas como `PROCESSO`, `VALOR_ORIGINAL`, `STATUS_PAGAMENTO` (ex.: “Quitado”).
- `Estado_Processos_Recebimento.xlsx` (opcional): espelho persistente do estado, com planilha `ESTADO`.

**Normalização E Pré‑Processamento**
- Leitura “tolerante” dos insumos (CSV/Excel), com limpeza básica de strings: trim em nomes/colunas; aplicação de `ALIASES` em “Consultor Interno” e “Representante-pedido”.
- `COLABORADORES` é mesclado a `CARGOS` para enriquecer atributos como `tipo_cargo`.
- Descoberta de “recebe por recebimento” através de:
  - `CARGOS.TIPO_COMISSAO == 'Recebimento'` e/ou `COLABORADORES.TIPO_COMISSAO == 'Recebimento'`;
  - fallback heurístico pelo nome do cargo contendo “receb”.

**Realizados (self.realizado)**
- `faturamento_linha`: soma de `Valor Realizado` por `Negócio`.
- `faturamento_individual`: soma de `Valor Realizado` por `Consultor Interno`.
- `conversao_linha`: soma de `Valor Orçado` por `Negócio`.
- `conversao_individual`: soma de `Valor Orçado` por `Consultor Interno`.
- `rentabilidade`: série indexada por `(linha, Grupo, Subgrupo, Tipo de Mercadoria)` com `rentabilidade_realizada_pct`.

**Regras De Comissão**
- Resolução por hierarquia (em `_get_regra_comissao(linha, grupo, subgrupo, tipo, cargo)`):
  - Match completo (linha+grupo+subgrupo+tipo+cargo);
  - Match com `subgrupo` nulo/`legacy_token`;
  - Match com `grupo` e `subgrupo` nulos/`legacy` para o mesmo `tipo`;
  - Regra `legacy_token` total (fallback). Cache por chave.
- Regra retorna ao menos `taxa_rateio_maximo_pct` (taxa) e `fatia_cargo_pct` (PE).

**Cálculo Do Fator De Correção (FC)**
- Para cada item e colaborador, carrega os pesos do cargo (`PESOS_METAS`). Componentes usuais:
  - `faturamento_linha` (por linha+tipo_mercadoria)
  - `conversao_linha` (por linha+tipo_mercadoria)
  - `faturamento_individual` (por colaborador)
  - `conversao_individual` (por colaborador)
  - `rentabilidade` (por linha+grupo+subgrupo+tipo_mercadoria; normalizada para decimal 0–1)
  - (quando presentes) `retencao_clientes` (aplicável, por exemplo, a Gerente Linha) e `meta_fornecedor_1/2` (metas YTD por moeda, com conversão cambial)
- Para cada componente com peso>0:
  - `realizado` (das séries) e `meta` (tabelas de metas) → `atingimento = realizado/meta`.
  - `atingimento_cap = min(atingimento, cap_atingimento_max)` (PARAMS).
  - `componente_fc = atingimento_cap * peso`.
- `fc_final = min(soma_componentes, cap_fc_max)` (PARAMS). Colunas de auditoria por componente são gravadas (peso_, realizado_, meta_, ating_, ating_cap_, comp_fc_ e, para fornecedor, moeda_).

**Cross‑Selling**
- Caso “Gerente Comercial-Pedido” seja um “Consultor Externo” sem atribuições para a linha do processo:
  - Opção A (SUBTRAIR): aplica uma redução na `taxa_rateio_aplicada` dos demais na taxa do cross-selling.
  - Opção B (PAGAR SEPARADAMENTE): remove o consultor externo do cálculo normal e paga linha separada com a taxa cs.
- Decisão pode vir de `PARAMS.cross_selling_default_option` quando sem interação.

**Cálculo Por Faturamento (COMISSOES_CALCULADAS)**
- Para cada item de `FATURADOS`:
  - Encontra colaboradores de gestão (`ATRIBUICOES` por contexto) e operacionais (Consultor Interno/Representante-pedido em `COLABORADORES`). Dedup e normalização de nomes.
  - Para cada colaborador:
    - Busca regra (`taxa_rateio`, `pe`).
    - Calcula FC (componentes e caps) → `fator_correcao_fc`.
    - `comissao_potencial_maxima = faturamento_item * taxa_rateio * pe`.
    - `comissao_calculada = comissao_potencial_maxima * fator_correcao_fc`.
- Colunas geradas (principais):
  - Identificação: `id_colaborador`, `nome_colaborador`, `cargo`.
  - Item/Processo: `processo`, `cod_produto`, `descricao_produto`.
  - Contexto: `linha`, `grupo`, `subgrupo`, `tipo_mercadoria`.
  - Cálculo: `faturamento_item`, `taxa_rateio_aplicada`, `percentual_elegibilidade_pe`, `fator_correcao_fc`, `comissao_potencial_maxima`, `comissao_calculada`.
  - Auditoria FC: `peso_fat_linha`, `realizado_fat_linha`, `meta_fat_linha`, `ating_fat_linha`, `ating_cap_fat_linha`, `comp_fc_fat_linha` (idem para `conv_linha`, `fat_ind`, `conv_ind`, `rentab`, e, se houver, `retencao`, `forn1`, `forn2` + `moeda_forn1/forn2`).
- Remoção de linhas dos colaboradores “que recebem por recebimento” da aba principal para não duplicar pagamento (eles aparecem na aba de recebimento).

**Adiantamentos Por Recebimento (COMISSOES_RECEBIMENTO)**
- Mapeia cada recebimento (`RECEBIMENTOS`) a um processo na `ANALISE_COMERCIAL_COMPLETA` (exato, substring, cliente+valor aproximado, truncamento numérico) e extrai contexto do processo.
- Identifica colaboradores do processo que “recebem por recebimento” (gestão/operacional conforme regras/atribuições).
- Fórmula (por linha): `comissao_calculada = VALOR_RECEBIDO * taxa_rateio * pe` (aqui FC=1.0).
- Colunas: `id_colaborador`, `nome_colaborador`, `cargo`, `processo`, `linha`, `grupo`, `subgrupo`, `tipo_mercadoria`, `faturamento_item` (valor recebido), `taxa_rateio_aplicada`, `percentual_elegibilidade_pe`, `fator_correcao_fc` (=1.0), `comissao_calculada`, `tipo_lancamento`, `observacao` (+ campos auxiliares de mapeamento, quando presentes).
- Atualiza `ESTADO`:
  - Cria/atualiza linha do processo: `VALOR_TOTAL_PROCESSO`, `TOTAL_PAGO_ACUMULADO += VALOR_RECEBIDO`, `TOTAL_ADIANTADO_COMISSAO += soma_comissao_recebimento_do_mes` (acumulativo), `STATUS_PAGAMENTO` (do arquivo `Status_Pagamentos_Processos`), `ULTIMA_ATUALIZACAO`.

**Estado Dos Processos (ESTADO)**
- Colunas: `PROCESSO`, `VALOR_TOTAL_PROCESSO`, `TOTAL_PAGO_ACUMULADO`, `TOTAL_ADIANTADO_COMISSAO`, `STATUS_PAGAMENTO`, `STATUS_RECONCILIACAO`, `STATUS_PROCESSO_ANALISE`, `ULTIMA_ATUALIZACAO`.
- Persistência: lê/escreve `Estado_Processos_Recebimento.xlsx` (planilha `ESTADO`).

**Reconciliação Retroativa (RECONCILIACAO)**
- Gatilho por processo: `STATUS_PAGAMENTO == 'Quitado'` e `STATUS_PROCESSO_ANALISE == 'Faturado'`, e `STATUS_RECONCILIACAO` não “Realizada/Concluida”.
- Para o mês/ano de emissão do processo:
  - Usa `preparar_dados_mensais.prepare_dataframes_for_month(mm, aaaa)` para montar os “realizados” históricos (faturados, conversões, YTD, retenção).
  - Carrega `rentabilidades/rentabilidade_{MM}_{AAAA}_agrupada.(xlsx|csv)`; normaliza e monta séries históricas.
  - Troca temporariamente `self.realizado` pelos históricos e recalcúla item a item, mas somente para colaboradores “que recebem por recebimento”.
  - Gera linhas detalhadas item-a-item (mesmas colunas de COMISSOES_CALCULADAS) e um resumo por processo: `COMISSAO_CORRETA_TOTAL`, `TOTAL_ADIANTAMENTOS_PAGOS`, `SALDO_FINAL_RECONCILIACAO`.
- Atualiza `ESTADO.STATUS_RECONCILIACAO = 'Realizada'` em sucesso.

**Saída (Excel + PDF)**
- Excel (`Comissoes_Calculadas_YYYYMMDD_HHMMSS.xlsx`):
  - `COMISSOES_CALCULADAS`: comissões de faturamento (sem os “recebimento-only”).
  - `RESUMO_COLABORADOR`: soma por colaborador (faturamento + recebimento).
  - `COMISSOES_RECEBIMENTO`: uma linha por pagamento mapeado; inclui contexto e, quando disponível, data de recebimento.
  - `RECONCILIACAO`: seção detalhada (linhas item-a-item) e, algumas linhas abaixo, tabela de resumo por processo.
  - `VALIDACAO`: log das mensagens de validação/aviso/erro.
  - `DEBUG_*`: visões auxiliares (ex.: `DEBUG_RECEBIMENTOS_RAW`, `DEBUG_RECEBIMENTOS`, `DEBUG_ENV`, `DEBUG_ANALISE_*`, `DEBUG_FORNECEDORES`).
  - `CROSS_SELLING_DECISIONS`: histórico de decisões (quando houver).
  - `ESTADO`: snapshot do estado atualizado.
- PDF (opcional, requer `reportlab`): relatório por item com explicações: regra aplicada, FC (componentes), fórmulas e valores.

**Parâmetros (PARAMS)**
- Chaves relevantes:
  - `cap_fc_max`: teto do FC (default 1.0).
  - `cap_atingimento_max`: teto do atingimento por componente (default 1.0).
  - `debug_terminal_fornecedores`, `debug_show_missing_fornecedores`, `sample_pages_pdf`, `max_pages_pdf`.
  - `cross_selling_default_option` (A|B).
  - `base_path`: base para localizar pastas históricas (`rentabilidades/`).

**Dependências**
- Python 3.x, `pandas`, `openpyxl`, `requests` (opcional para câmbio), `reportlab` (opcional para PDF).

**Assunções E Normalizações**
- Comparações textuais normalizadas (trim; case-insensitive em pontos críticos; suporte a aliases).
- Datas de emissão podem vir com variações; conversão defensiva (`dayfirst` quando aplicável).
- Fallbacks conservadores quando arquivos faltam: DataFrames vazios e logs em `VALIDACAO`.

**Limitações Conhecidas**
- Reconciliação depende de localizar rentabilidade histórica por Mês/Ano (ou fallback se ausente).
- Mapeamento de recebimentos pode cair em heurísticas quando não há match exato; nesses casos, registros são sinalizados em `DEBUG_RECEBIMENTOS`.
- Componentes de fornecedor exigem YTD por moeda e taxas cambiais médias; se ausentes, componente pode ficar 0.

**Execução**
- Passos típicos:
  - Rodar scripts de limpeza para o mês/ano desejado (geram `Recebimentos_do_Mes.xlsx` e `Status_Pagamentos_Processos.xlsx`).
  - Executar o robô (interativo): informar mês/ano → o robô roda o preparador em modo validação → carrega dados → executa cálculos → salva Excel e, opcionalmente, PDF.
- Saídas são gravadas na raiz do projeto; o nome do Excel inclui timestamp.

**Diagnóstico E Depuração**
- `VALIDACAO`: concentre-se em avisos de “Meta não encontrada”, “Falha ao ler…”, “processo mapeado via …”, “colaboradores detectados para recebimento…”.
- Confira nas abas de saída as colunas de cálculo e as de auditoria do FC para identificar rapidamente se o zero veio de `taxa_rateio`, `pe`, `faturamento_item` ou `fc`.
- Utilize os DEBUG_* para checar headers, amostras e ambiente (linhas e colaboradores marcados como recebimento).

**Fórmulas‑Chave**
- `comissao_potencial_maxima = faturamento_item * taxa_rateio_aplicada * percentual_elegibilidade_pe`
- `comissao_calculada = comissao_potencial_maxima * fator_correcao_fc`
- Recebimento: `comissao_calculada = valor_recebido * taxa_rateio_aplicada * percentual_elegibilidade_pe` (FC=1.0)
- Reconciliação: igual ao faturamento, mas com `self.realizado` substituído por séries históricas do mês/ano do faturamento.
