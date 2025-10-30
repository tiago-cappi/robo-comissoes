# 🧪 Como Testar o Robô Refatorado

## Guia Rápido de Testes

Este guia explica como testar o robô após a refatoração para garantir que tudo funciona corretamente.

---

## ✅ 1. Testes Unitários (RECOMENDADO FAZER PRIMEIRO)

### Executar Todos os Testes

```bash
# Ir para a pasta do projeto
cd "C:\Users\Meu Computador\Desktop\Clean Trabalho\robo-comissoes"

# Testar utilitários
python tests/test_utils_normalization.py
python tests/test_utils_column_finder.py
python tests/test_utils_date_parser.py

# Testar modelos
python tests/test_process_state.py

# Testar serviços
python tests/test_payment_services.py
python tests/test_reconciliation_services.py
```

**Resultado esperado:** Todos os testes devem passar ✅

**Se algum teste falhar:**
1. Copiar a mensagem de erro
2. Verificar se os arquivos de módulos estão no lugar certo
3. Verificar imports

---

## 🚀 2. Teste de Integração Básico

### Executar o Robô Completo

```bash
python calculo_comissoes.py
```

**O que observar:**

✅ **Deve executar sem erros**
- Todas as fases devem completar
- Nenhuma exceção deve ser lançada

✅ **Deve gerar saídas**
- Arquivo Excel: `Comissoes_Calculadas_YYYYMMDD_HHMMSS.xlsx`
- Arquivo de estado: `Estado_Processos_Recebimento.xlsx`

✅ **Deve mostrar logs**
```
[Recebimentos] Processados: X/Y
[Recebimentos] Taxa de mapeamento: XX.X%
[Reconciliação] Processos: X
```

---

## 📊 3. Validação de Saída

### Comparar Excel Gerado

1. **Abrir o Excel gerado:**
   - `Comissoes_Calculadas_YYYYMMDD_HHMMSS.xlsx`

2. **Verificar abas existem:**
   - ✅ `COMISSOES_CALCULADAS`
   - ✅ `RESUMO_COLABORADOR`
   - ✅ `COMISSOES_RECEBIMENTO` (se houver recebimentos)
   - ✅ `RECONCILIACAO` (se houver processos elegíveis)
   - ✅ `VALIDACAO`
   - ✅ `ESTADO`

3. **Verificar valores:**
   - Abrir Excel da versão anterior (se houver)
   - Comparar valores de comissões calculadas
   - **Devem ser idênticos** (diferenças < R$ 0,01)

### Checklist de Validação

| Item | Verificação | Status |
|------|-------------|--------|
| Excel gerado | Arquivo criado? | ⬜ |
| Abas presentes | Todas as abas existem? | ⬜ |
| COMISSOES_CALCULADAS | Valores preenchidos? | ⬜ |
| COMISSOES_RECEBIMENTO | Se houver recebimentos, linhas criadas? | ⬜ |
| RECONCILIACAO | Se houver elegíveis, cálculos corretos? | ⬜ |
| ESTADO | Processos atualizados? | ⬜ |
| VALIDACAO | Sem erros críticos? | ⬜ |

---

## 🔍 4. Testes de Casos Extremos

### Teste 1: Sem Recebimentos

1. Renomear temporariamente `Recebimentos_do_Mes.xlsx`
2. Executar: `python calculo_comissoes.py`
3. **Resultado esperado:** 
   - Executa sem erros
   - Log: "[DEBUG] Nenhum recebimento encontrado."
   - Aba `COMISSOES_RECEBIMENTO` vazia

### Teste 2: Sem Processos para Reconciliar

1. Executar: `python calculo_comissoes.py`
2. Se não houver processos quitados e faturados
3. **Resultado esperado:**
   - Executa sem erros
   - Log: "[Reconciliação] Nenhum processo elegível"

### Teste 3: Estado Vazio

1. Renomear temporariamente `Estado_Processos_Recebimento.xlsx`
2. Executar: `python calculo_comissoes.py`
3. **Resultado esperado:**
   - Cria novo arquivo de estado
   - Executa normalmente

---

## 🛠️ 5. Troubleshooting

### Problema: ImportError

**Erro:** `ModuleNotFoundError: No module named 'models'`

**Solução:**
```bash
# Verificar estrutura de pastas
dir utils
dir models
dir services
dir tests

# Deve ter __init__.py em cada pasta
```

### Problema: Valores Diferentes

**Erro:** Comissões calculadas diferem da versão anterior

**Solução:**
1. Verificar se os arquivos de entrada são os mesmos
2. Comparar logs de mapeamento
3. Verificar `VALIDACAO` no Excel para avisos

### Problema: Erro ao Processar Recebimentos

**Erro:** `[ERRO] Erro ao processar recebimentos: ...`

**Solução:**
1. Verificar formato do arquivo `Recebimentos_do_Mes.xlsx`
2. Verificar colunas necessárias: PROCESSO, VALOR_RECEBIDO
3. Ver aba `VALIDACAO` para detalhes

### Problema: Erro ao Reconciliar

**Erro:** `[ERRO] Erro ao executar reconciliações: ...`

**Solução:**
1. Verificar se pasta `rentabilidades/` existe
2. Verificar arquivos de rentabilidade histórica
3. Ver aba `VALIDACAO` para detalhes

---

## 🔄 6. Rollback (Se Necessário)

Se houver problemas sérios, você pode voltar para a versão anterior:

```bash
# Windows PowerShell
copy calculo_comissoes_backup_20251029_233238.py calculo_comissoes.py
```

**Backup criado em:** `calculo_comissoes_backup_20251029_233238.py`

---

## 📈 7. Teste de Performance (Opcional)

### Medir Tempo de Execução

```python
import time

inicio = time.time()
# Executar robô
fim = time.time()

print(f"Tempo total: {fim - inicio:.2f} segundos")
```

**Esperado:** Tempo similar ou ligeiramente melhor que versão anterior

---

## ✅ Checklist Final

- [ ] Todos os testes unitários passam (39/39)
- [ ] Robô executa sem erros
- [ ] Excel é gerado corretamente
- [ ] Todas as abas estão presentes
- [ ] Valores de comissões são corretos
- [ ] Logs fazem sentido
- [ ] Estado é atualizado corretamente
- [ ] Testes de casos extremos passam

---

## 🎯 Resultado Esperado

Ao final dos testes, você deve ter:

✅ **39 testes unitários** passando  
✅ **Robô executando** sem erros  
✅ **Excel gerado** com todas as abas  
✅ **Valores corretos** (idênticos à versão anterior)  
✅ **Logs informativos** mostrando processamento  
✅ **Estado atualizado** corretamente

---

## 📞 Se Tudo Passar

**Parabéns!** 🎉 O robô refatorado está funcionando perfeitamente!

**Próximos passos:**
1. Usar o robô normalmente
2. Monitorar primeiras execuções
3. Reportar qualquer comportamento estranho
4. Aproveitar a nova arquitetura modular!

---

## 📞 Se Houver Problemas

1. **Verificar backup existe:**
   - `calculo_comissoes_backup_20251029_233238.py`

2. **Ler documentação:**
   - `PROGRESSO_REFATORACAO.md` - Visão geral
   - `FASE5_RESUMO.md` - Detalhes de integração
   - `services/README.md` - Documentação de serviços

3. **Revisar logs:**
   - Aba `VALIDACAO` no Excel
   - Saída do terminal

4. **Rollback se necessário:**
   ```bash
   copy calculo_comissoes_backup_20251029_233238.py calculo_comissoes.py
   ```

---

**Criado em:** 30/10/2025  
**Versão:** 1.0  
**Status:** ✅ Pronto para uso

