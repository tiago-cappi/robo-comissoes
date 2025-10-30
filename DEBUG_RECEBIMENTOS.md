# 🔍 Debug de Recebimentos e Reconciliações

## Problema
O Excel é gerado, mas não há comissões por recebimento nem reconciliações.

## Logs de Debug Adicionados

Adicionei logs detalhados para investigar:
1. Quantos colaboradores recebem por recebimento
2. Quantos recebimentos foram processados
3. Se os recebimentos foram mapeados para processos
4. Quantos colaboradores foram encontrados
5. Se os colaboradores estão sendo filtrados corretamente

---

## 🧪 Como Executar com Debug

Execute o robô **com logs verbosos ativados**:

### Windows PowerShell
```powershell
$env:COMISSOES_VERBOSE="1"
python calculo_comissoes.py --mes 9 --ano 2025
```

### Windows CMD
```cmd
set COMISSOES_VERBOSE=1
python calculo_comissoes.py --mes 9 --ano 2025
```

---

## 📋 O Que Observar na Saída

Procure pelas linhas de DEBUG:

### 1. Colaboradores que Recebem por Recebimento
```
[DEBUG Recebimentos] Colaboradores que recebem por recebimento: {'Nome1', 'Nome2', 'Nome3'}
```
**Esperado:** Deve mostrar pelo menos 3 nomes (André Caramello, Neimar, Gabriel Prado)

### 2. Total de Recebimentos
```
[DEBUG Recebimentos] Total de recebimentos: 4
```
**Esperado:** Deve mostrar 4 recebimentos

### 3. Processamento
```
[DEBUG Recebimentos] Iniciando processamento...
[DEBUG Calculator] Processo: XXXXX, Valor: YYYY
[DEBUG Calculator] Contexto: {...}
[DEBUG Calculator] Set recebe_por_recebimento_norm: {...}
[DEBUG Calculator] Colaboradores encontrados: N, detalhes: [...]
```
**O que verificar:**
- Se o processo foi mapeado
- Se o contexto tem linha, grupo, subgrupo
- Se os nomes normalizados estão corretos
- Quantos colaboradores foram encontrados

### 4. Comissões Geradas
```
[DEBUG Recebimentos] Comissões geradas: N
```
**Esperado:** Deve ser > 0

---

## 🔎 Possíveis Causas

### Causa 1: Nomes Não Estão Normalizados Corretamente
Se os nomes em `self.recebe_por_recebimento` não estão sendo normalizados do mesmo jeito que os nomes dos colaboradores, eles não vão fazer match.

**Solução:** Ver os logs de normalização.

### Causa 2: Recebimentos Não Estão Sendo Mapeados
Se os processos dos recebimentos não existem na análise comercial, não gera comissão.

**Solução:** Ver se os processos estão no arquivo `Analise_Comercial_Completa.csv`.

### Causa 3: Colaboradores Não Estão nas Atribuições
Se os colaboradores não têm atribuições para as linhas dos processos, não aparecerão.

**Solução:** Verificar arquivo `ATRIBUICOES` no Excel de regras.

### Causa 4: Contexto do Processo Vazio
Se linha/grupo/subgrupo/tipo estão vazios, não encontra atribuições.

**Solução:** Ver o contexto no log `[DEBUG Calculator] Contexto`.

---

## 📤 Próximos Passos

1. Execute com `COMISSOES_VERBOSE=1`
2. Copie toda a saída do terminal
3. Me envie para analisar
4. Vou identificar o problema exato

---

**Criado em:** 30/10/2025  
**Status:** Aguardando execução com debug

