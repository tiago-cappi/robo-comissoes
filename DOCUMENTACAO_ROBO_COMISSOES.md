**Visão Geral**
- Robô que calcula comissões por faturamento (item a item), comissões por recebimento (a nível de processo via médias ponderadas) e reconciliações no mês do faturamento, gerando um Excel consolidado (cálculo, resumo e depuração) e um PDF opcional.
- Fluxo de alto nível (nova lógica): carrega dados → normaliza/parametriza → calcula “realizados” → calcula métricas TCMP/FCMP e reconciliações do mês → calcula comissões por recebimento (usando TCMP/FCMP) → calcula comissões por faturamento (item a item; inalterado) → gera saídas (Excel + PDF + logs).

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
- `Estado_Processos_Recebimento.xlsx` (opcional): espelho persistente do estado, com planilha `ESTADO`.
- `Análise Financeira.xlsx` (obrigatório para recebimentos): fonte única de pagamentos (adiantamentos e parcelas). Regras de vinculação:
  - Se `Documento` começar com `COT`: é Adiantamento; `PROCESSO` = sufixo numérico após `COT` (ex.: `COT123456` → `123456`).
  - Caso contrário: Pagamento Regular; `DOCUMENTO_NORMALIZADO` = 6 primeiros dígitos do `Documento`, vinculado à coluna `Numero NF` na Análise Comercial.

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

**Comissões Por Recebimento (Nova Lógica - COMISSOES_RECEBIMENTO)**
- Sempre calculadas a nível de processo usando médias ponderadas:
  - `TCMP` (Taxa de Comissão Média Ponderada por colaborador): média ponderada pelo valor do item das taxas por item (`taxa_rateio_maximo_pct * fatia_cargo_pct`).
  - `FCMP` (Fator de Correção Médio Ponderado por colaborador): média ponderada pelo valor do item dos FCs por item (capados por `cap_fc_max`).
- Antes do faturamento (Adiantamentos; `Documento` iniciando com `COT`):
  - Comissão por colaborador: `comissao = valor_adiantado * TCMP_colaborador` (FC=1.0).
  - Atualiza `ESTADO`: `TOTAL_ANTECIPACOES`/`TOTAL_PAGO_ACUMULADO` (valor) e `TOTAL_ADIANTADO_COMISSAO` (soma das comissões pagas no adiantamento).
- Após o faturamento (Pagamentos Regulares):
  - Comissão por colaborador: `comissao = valor_parcela * TCMP_colaborador * FCMP_colaborador` (métricas salvas no estado no mês do faturamento).

**Estado Dos Processos (ESTADO)**
- Colunas principais:
  - `PROCESSO`, `VALOR_TOTAL_PROCESSO`, `TOTAL_ANTECIPACOES`, `TOTAL_PAGAMENTOS_REGULARES`, `TOTAL_PAGO_ACUMULADO`, `TOTAL_ADIANTADO_COMISSAO`,
  - `STATUS_PAGAMENTO`, `STATUS_RECONCILIACAO`, `STATUS_PROCESSO_ANALISE`,
  - `STATUS_CALCULO_MEDIAS`, `MES_ANO_FATURAMENTO`, `TCMP` (JSON por colaborador), `FCMP` (JSON por colaborador),
  - `ULTIMA_ATUALIZACAO`.
- Persistência: lê/escreve `Estado_Processos_Recebimento.xlsx` (planilha `ESTADO`).

**Reconciliação (no mês do Faturamento)**
- Gatilho: o processo aparece como `FATURADO` na Análise Comercial para o mês/ano de apuração.
- Ações para todo processo faturado:
  - Calcular e persistir `TCMP` e `FCMP` por colaborador (para uso em parcelas futuras).
- Reconciliação somente se houve adiantamentos:
  - `Saldo de Reconciliação (processo)` = soma_{colab}(`Total_Adiantado` × w_colab × (`FCMP_colab` − 1)), onde w_colab é a proporção do `TCMP_colab` no processo.
  - O saldo (≤ 0; pois `cap_fc_max` ≤ 1) é aplicado no mês do faturamento e exibido no resumo.

**Saída (Excel + PDF)**
- Excel (`Comissoes_Calculadas_YYYYMMDD_HHMMSS.xlsx`):
  - `COMISSOES_CALCULADAS`: comissões de faturamento (item a item).
  - `RESUMO_COLABORADOR`: soma por colaborador (faturamento + recebimento + ajustes de reconciliação).
  - `COMISSOES_RECEBIMENTO`: linhas por pagamento (adiantamento: TCMP; parcela: TCMP*FCMP).
  - `RECONCILIACAO`: resumo por processo com saldos aplicados no mês do faturamento.
  - `VALIDACAO` e `ESTADO`: logs e snapshot do estado.
- PDF (opcional, requer `reportlab`): relatório por item (faturamento).

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
  - Executar o robô (interativo): informar mês/ano → carregar dados → calcular realizados → calcular métricas/reconciliações (mês) → comissões por recebimento → comissões por faturamento → gerar Excel/PDF.
- Saídas são gravadas na raiz do projeto; o nome do Excel inclui timestamp.

**Diagnóstico E Depuração**
- `VALIDACAO`: concentre-se em avisos de “Meta não encontrada”, “Falha ao ler…”, “processo mapeado via …”, “colaboradores detectados para recebimento…”.
- Confira nas abas de saída as colunas de cálculo e as de auditoria do FC para identificar rapidamente se o zero veio de `taxa_rateio`, `pe`, `faturamento_item` ou `fc`.
- Utilize os DEBUG_* para checar headers, amostras e ambiente (linhas e colaboradores marcados como recebimento).

**Fórmulas‑Chave**
- Faturamento (inalterado): 
  - `comissao_potencial_maxima = faturamento_item * taxa_rateio_aplicada * percentual_elegibilidade_pe`
  - `comissao_calculada = comissao_potencial_maxima * fator_correcao_fc`
- Recebimento (nova lógica):
  - Adiantamento: `comissao = valor_adiantado * TCMP_colaborador` (FC=1.0)
  - Parcela pós-faturamento: `comissao = valor_parcela * TCMP_colaborador * FCMP_colaborador`
- Reconciliação (mês do faturamento; somente se houve adiantamentos):
  - `saldo_processo = Σ_colab ( Total_Adiantado × w_colab × (FCMP_colab − 1) )`, onde `w_colab = TCMP_colab / Σ(TCMP)`.
