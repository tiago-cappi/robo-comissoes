# Utilitários do Robô de Comissões

Este diretório contém módulos utilitários reutilizáveis que eliminam duplicação de código e fornecem interfaces consistentes para operações comuns.

## Módulos

### `normalization.py`
Funções para normalização de textos, processos e colunas.

**Principais funções:**
- `normalize_text(s)`: Normaliza texto (remove acentos, BOM, uppercase, trim)
- `normalize_process_id(val)`: Normaliza IDs de processos (tratamento consistente de int/float/str)
- `normalize_column_name(col)`: Normaliza nomes de colunas (lowercase, sem espaços)

**Uso:**
```python
from utils.normalization import normalize_text, normalize_process_id

# Comparação case-insensitive
if normalize_text(cargo) == "GERENTE COMERCIAL":
    ...

# Normalizar ID de processo
proc_id = normalize_process_id(999999.0)  # retorna "999999"
```

### `column_finder.py`
Interface para busca de colunas em DataFrames com nomes variados.

**Classe principal:** `ColumnFinder`

**Uso:**
```python
from utils.column_finder import ColumnFinder

finder = ColumnFinder(df)

# Buscar uma coluna por aliases
processo_col = finder.find_column(['processo', 'id processo', 'id_processo'])

# Buscar múltiplas colunas
cols = finder.find_all_columns({
    'processo': ['processo', 'id processo'],
    'valor': ['valor realizado', 'faturamento']
})
```

### `date_parser.py`
Parsing robusto de datas com detecção automática de formato.

**Principais funções:**
- `parse_date_smart(series)`: Parse série de datas com detecção de formato ISO/BR
- `parse_date_flexible(date_value)`: Parse individual com múltiplas estratégias
- `detect_timestamp_nanoseconds(date_value)`: Detecta timestamps Unix em nanosegundos
- `extract_year_month(date_value)`: Extrai tupla (ano, mês)

**Uso:**
```python
from utils.date_parser import parse_date_smart, parse_date_flexible

# Parsear coluna de datas
df['data'] = parse_date_smart(df['Dt Emissão'])

# Parsear valor individual
data = parse_date_flexible('15/01/2025')  # pd.Timestamp('2025-01-15')
```

## Testes

Execute os testes para verificar que os módulos funcionam:

```bash
python tests/test_utils_normalization.py
python tests/test_utils_column_finder.py
python tests/test_utils_date_parser.py
```

## Benefícios

✅ **Eliminação de duplicação**: Código de normalização/busca centralizado  
✅ **Consistência**: Mesma lógica aplicada em todo o robô  
✅ **Testabilidade**: Funções isoladas e fáceis de testar  
✅ **Manutenibilidade**: Mudanças em um só lugar  
✅ **Documentação**: Docstrings completas com exemplos

