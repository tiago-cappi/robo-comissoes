# Início Rápido - Frontend Robô de Comissões

## 1. Configuração Inicial

### Adapter FastAPI

```powershell
# 1. Navegar para a pasta do adapter
cd frontend\adapter

# 2. Instalar dependências
pip install -r requirements.txt

# 3. Criar arquivo .env (copiar do exemplo)
copy .env.example .env

# 4. Editar .env e configurar o caminho do robô
# ROBO_ROOT_PATH=C:\caminho\para\robo-comissoes
```

### Frontend React

```powershell
# 1. Navegar para a pasta do frontend
cd frontend

# 2. Instalar dependências
npm install
# ou
yarn install
```

## 2. Executar Aplicação

### Terminal 1: Adapter FastAPI

**Opção 1: Script automático (recomendado)**
```powershell
cd frontend\adapter
.\run.ps1
# ou no CMD:
.\run.bat
```

**Opção 2: Manualmente**
```powershell
cd frontend\adapter

# Se uvicorn estiver no PATH:
uvicorn app:app --reload --port 8000

# Se não estiver (fallback automático):
python -m uvicorn app:app --reload --port 8000
```

**Nota:** O script `.run.ps1` verifica automaticamente e usa o método disponível.

Verificar: `http://localhost:8000/docs`

### Terminal 2: Frontend React

```powershell
cd frontend
npm start
```

A aplicação abrirá automaticamente em: `http://localhost:3000`

## 3. Primeiros Passos

1. **Configurar Regras**: Acesse "Regras" e edite `Regras_Comissoes.xlsx`
2. **Fazer Uploads**: Acesse "Uploads" e envie os arquivos ERP
3. **Executar Cálculo**: Acesse "Executar Cálculo" e escolha mês/ano
4. **Ver Resultados**: Acesse "Resultados" após o cálculo concluir

## 4. Troubleshooting

**Erro: "Arquivo não encontrado"**
- Verifique se `ROBO_ROOT_PATH` no `.env` está correto
- Certifique-se de que o caminho aponta para a pasta raiz do robô

**Erro: "Porta já em uso"**
- Altere a porta no uvicorn: `--port 8001`
- Atualize `src/services/api.js` com a nova porta

**CORS errors**
- Verifique se o adapter está rodando em `http://localhost:8000`
- Confirme que `CORS_ORIGINS` no adapter inclui `http://localhost:3000`

## 5. Estrutura de Arquivos

```
frontend/
├── adapter/              # Backend FastAPI
│   ├── app.py            # Aplicação principal
│   ├── requirements.txt  # Dependências Python
│   ├── .env              # Configuração (criar a partir do exemplo)
│   └── run.bat           # Script de inicialização (Windows)
├── src/
│   ├── components/       # Componentes reutilizáveis
│   ├── pages/            # Páginas principais
│   ├── services/         # Serviços API
│   └── App.js            # Componente principal
├── package.json          # Dependências Node.js
└── README.md             # Documentação completa
```

