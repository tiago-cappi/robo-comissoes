# Estrutura do Frontend - Robô de Comissões

## Visão Geral

O frontend é uma aplicação React moderna com Ant Design, conectada a um adapter FastAPI que orquestra o robô Python existente.

## Arquitetura

```
┌─────────────────┐
│   React App     │  (Frontend - http://localhost:3000)
│   (Ant Design)  │
└────────┬────────┘
         │ HTTP Requests
         ▼
┌─────────────────┐
│  FastAPI        │  (Adapter - http://localhost:8000)
│  (Orquestração) │
└────────┬────────┘
         │ Subprocess / File I/O
         ▼
┌─────────────────┐
│  Robô Python    │  (Backend existente - não modificado)
│  calculo_*.py   │
└─────────────────┘
```

## Estrutura de Arquivos

```
frontend/
├── adapter/                    # Backend FastAPI
│   ├── app.py                  # Aplicação principal com todos os endpoints
│   ├── requirements.txt        # Dependências Python
│   ├── .env.example            # Exemplo de configuração
│   ├── run.bat                 # Script de inicialização (Windows CMD)
│   ├── run.ps1                 # Script de inicialização (PowerShell)
│   └── README.md               # Documentação do adapter
│
├── src/                        # Frontend React
│   ├── components/             # Componentes reutilizáveis
│   │   ├── MainLayout.js       # Layout principal com sidebar
│   │   └── BulkApplyModal.js   # Modal para aplicação em massa
│   │
│   ├── pages/                  # Páginas principais
│   │   ├── RegrasPage.js       # Editor de Regras_Comissoes.xlsx
│   │   ├── UploadsPage.js      # Upload de arquivos ERP
│   │   ├── ExecutarPage.js     # Execução com progresso
│   │   └── ResultadosPage.js   # Visualização de resultados
│   │
│   ├── services/               # Serviços de API
│   │   └── api.js              # Cliente axios com todos os endpoints
│   │
│   ├── App.js                  # Componente raiz com roteamento
│   ├── index.js                # Entry point
│   └── index.css               # Estilos globais
│
├── public/                     # Arquivos estáticos
│   └── index.html              # HTML base
│
├── package.json                # Dependências e scripts Node.js
├── README.md                   # Documentação principal
├── INICIO_RAPIDO.md            # Guia de início rápido
└── .gitignore                  # Arquivos ignorados pelo git
```

## Fluxo de Dados

### 1. Editor de Regras
```
Usuário edita → React (RegrasPage)
  ↓
API call → FastAPI (app.py)
  ↓
Lê/Escreve → Regras_Comissoes.xlsx (pasta raiz do robô)
```

### 2. Uploads
```
Usuário seleciona arquivo → React (UploadsPage)
  ↓
Upload → FastAPI (endpoint /upload/*)
  ↓
Salva arquivo → Pasta raiz do robô (nome exato preservado)
```

### 3. Execução
```
Usuário clica "Calcular" → React (ExecutarPage)
  ↓
POST /calcular → FastAPI
  ↓
Dispara subprocesso → calculo_comissoes.py
  ↓
Python escreve → progress.json
  ↓
Polling (GET /progresso) → React atualiza UI
  ↓
Ao concluir → Link para download e navegação para Resultados
```

### 4. Resultados
```
Usuário acessa Resultados → React (ResultadosPage)
  ↓
GET /resultado/abas → FastAPI
  ↓
Lê → Comissoes_Calculadas_*.xlsx mais recente
  ↓
Retorna dados paginados → React renderiza tabela
```

## Componentes Principais

### MainLayout
- Sidebar com navegação
- Header com título
- Container principal para páginas

### RegrasPage
- Lista abas dinamicamente
- Tabela editável inline
- Filtros e busca global
- Aplicação em massa via BulkApplyModal
- Preservação de ordem de colunas

### UploadsPage
- Cards para cada tipo de upload
- Validação de formato
- Feedback visual de sucesso/erro

### ExecutarPage
- Formulário mês/ano
- Barra de progresso
- Logs em tempo real
- Polling de progresso
- Download do resultado

### ResultadosPage
- Tabs para cada aba do Excel
- Tabela paginada com filtros
- Presets de colunas
- Drawer com detalhes do item
- Tooltips com glossário

## Integração com Progresso

O robô Python deve escrever um arquivo `progress.json` na pasta raiz:

```json
{
  "job_id": "uuid-do-job",
  "percent": 75.5,
  "etapa": "Calculando comissões por faturamento",
  "mensagens": ["Processando item 100/500", "..."],
  "status": "em_andamento" | "concluido" | "erro"
}
```

O adapter lê este arquivo e serve via `GET /progresso/{jobId}`.

**Nota**: Se o robô Python não escrever `progress.json`, o adapter simula um progresso básico.

## Endpoints do Adapter

### Regras
- `GET /regras/abas` - Lista abas
- `GET /regras/aba/{nome}` - Lê aba com paginação/filtros
- `POST /regras/aba/{nome}/save` - Salva alterações
- `POST /regras/aba/{nome}/apply-bulk` - Aplicação em massa

### Uploads
- `POST /upload/analise` - Analise_Comercial_Completa
- `POST /upload/fin_adcli` - fin_adcli_pg_m3.xls
- `POST /upload/fin_conci` - fin_conci_adcli_m3.xls
- `POST /upload/analise_financeira` - Análise Financeira.xlsx

### Execução
- `POST /calcular?mes=X&ano=Y` - Inicia cálculo
- `GET /progresso/{jobId}` - Consulta progresso

### Resultados
- `GET /resultado/abas` - Lista abas do resultado
- `GET /resultado/aba/{nome}` - Lê aba com paginação
- `GET /baixar/resultado` - Download do Excel completo

### Utilitários
- `GET /health` - Health check

## Preservação de Dados

⚠️ **IMPORTANTE**: O adapter preserva:
- Ordem original das colunas do Excel
- Nomes exatos das colunas
- Estrutura das abas
- Formato dos dados

O adapter **NÃO**:
- Adiciona colunas não existentes
- Remove colunas existentes
- Altera tipos de dados
- Modifica a lógica do robô Python

## Performance

- **Paginação servidor**: Reduz carga de dados
- **Virtualização**: Tabelas grandes renderizam apenas itens visíveis
- **Cache**: Regras de comissão são cacheadas no Python
- **Polling otimizado**: 1.5s de intervalo para progresso

## Segurança

- CORS configurado para localhost apenas
- Validação de tipos de arquivo nos uploads
- Sanitização de inputs
- Path validation para evitar directory traversal

## Extensibilidade

Para adicionar novas funcionalidades:

1. **Novo endpoint**: Adicionar em `frontend/adapter/app.py`
2. **Novo serviço**: Adicionar em `frontend/src/services/api.js`
3. **Nova página**: Criar em `frontend/src/pages/` e adicionar rota em `App.js`
4. **Novo componente**: Criar em `frontend/src/components/`

