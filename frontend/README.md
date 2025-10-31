# Frontend Robô de Comissões

Frontend completo para o robô de cálculo de comissões, desenvolvido em React + Ant Design com backend adapter FastAPI.

## Estrutura do Projeto

```
frontend/
├── adapter/          # Backend FastAPI (orquestração)
│   ├── app.py        # Aplicação principal
│   ├── requirements.txt
│   └── README.md
├── src/              # Frontend React
│   ├── components/   # Componentes reutilizáveis
│   ├── pages/        # Páginas principais
│   ├── services/     # Serviços API
│   └── ...
├── package.json
└── README.md         # Este arquivo
```

## Pré-requisitos

- Python 3.8+ (para o adapter FastAPI)
- Node.js 16+ e npm/yarn (para o frontend React)
- Windows (ambiente de desenvolvimento)

## Configuração

### 1. Configurar caminho do robô

Edite `frontend/adapter/.env` (ou crie se não existir):

```env
ROBO_ROOT_PATH=C:\Users\Meu Computador\Desktop\Robô-comissões\robo-comissoes
```

Ou defina variável de ambiente:
```powershell
$env:ROBO_ROOT_PATH="C:\Users\Meu Computador\Desktop\Robô-comissões\robo-comissoes"
```

### 2. Instalar dependências do adapter

```powershell
cd frontend/adapter
pip install -r requirements.txt
```

### 3. Instalar dependências do frontend

```powershell
cd frontend
npm install
# ou
yarn install
```

## Execução

### Terminal 1: Iniciar adapter FastAPI

```powershell
cd frontend/adapter
uvicorn app:app --reload --port 8000
```

O adapter estará disponível em: `http://localhost:8000`
Documentação OpenAPI: `http://localhost:8000/docs`

### Terminal 2: Iniciar frontend React

```powershell
cd frontend
npm start
# ou
yarn start
```

O frontend estará disponível em: `http://localhost:3000`

## Funcionalidades

### 1. Editor de Regras
- Edição inline de `Regras_Comissoes.xlsx`
- Suporte a todas as abas
- Filtros, ordenação, paginação
- Aplicação em massa

### 2. Uploads
- Upload de arquivos ERP
- Validação de formato e tamanho
- Feedback visual

### 3. Executar Cálculo
- Seleção de mês/ano
- Execução do robô Python
- Barra de progresso e logs
- Download do resultado

### 4. Resultados
- Visualização de todas as abas
- Filtros avançados
- Presets de colunas
- Exportação CSV

## Progresso da Execução

O sistema de progresso funciona assim:

1. Ao iniciar o cálculo, o adapter dispara `calculo_comissoes.py` como subprocesso
2. O processo escreve `progress.json` na pasta raiz do robô:
   ```json
   {
     "job_id": "uuid",
     "percent": 75,
     "etapa": "Calculando comissões por faturamento",
     "mensagens": ["...", "..."],
     "status": "em_andamento"
   }
   ```
3. O frontend faz polling em `GET /progresso/{jobId}` a cada 1-2 segundos
4. Ao finalizar, `status: "concluido"` e link para download

## Notas Importantes

- **Não altera código Python existente**: O adapter apenas orquestra via subprocesso
- **Arquivos na raiz**: Todos os arquivos são lidos/escritos na pasta raiz do robô
- **Nomes exatos**: Os nomes dos arquivos devem ser exatamente como especificado
- **Preservação de formato**: O adapter preserva ordem de colunas e abas do Excel

## Desenvolvimento

### Build de produção

Frontend:
```powershell
npm run build
```

Adapter:
```powershell
# Já está pronto para produção (sem build necessário)
```

## Troubleshooting

**Erro: "Arquivo não encontrado"**
- Verifique se `ROBO_ROOT_PATH` está correto
- Certifique-se de que o caminho aponta para a pasta raiz do robô

**Erro: "Porta já em uso"**
- Altere a porta no `uvicorn` (ex.: `--port 8001`)
- Atualize `src/services/api.ts` com a nova porta

**Erro: "CORS"**
- Verifique se o adapter está rodando
- Confirme que `CORS_ORIGINS` no adapter inclui `http://localhost:3000`

