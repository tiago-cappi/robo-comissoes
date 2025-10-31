# Solução de Problemas Comuns

## Erro: "uvicorn não é reconhecido"

**Solução 1: Usar Python diretamente**
```powershell
cd frontend\adapter
python -m uvicorn app:app --reload --port 8000
```

**Solução 2: Instalar dependências primeiro**
```powershell
cd frontend\adapter
pip install -r requirements.txt
uvicorn app:app --reload --port 8000
```

**Solução 3: Usar o script (faz tudo automaticamente)**
```powershell
cd frontend\adapter
.\run.ps1
# ou
.\run.bat
```

## Erro: "Invalid options object. Dev Server has been initialized..."

Este erro ocorre quando há um problema com a configuração do webpack dev server.

**Solução:**
1. O arquivo `.env` foi criado com `DANGEROUSLY_DISABLE_HOST_CHECK=true`
2. O `proxy` foi removido do `package.json` (substituído por `setupProxy.js`)
3. Execute:
```powershell
cd frontend
npm install
npm start
```

Se ainda houver problemas:
```powershell
# Limpar cache e reinstalar
rm -rf node_modules package-lock.json
npm install
npm start
```

## Erro: "FastAPI não encontrado" ou "ModuleNotFoundError"

**Solução:**
```powershell
cd frontend\adapter
pip install -r requirements.txt
```

Se usar ambiente virtual:
```powershell
# Criar venv (opcional)
python -m venv venv

# Ativar venv
.\venv\Scripts\Activate.ps1
# ou
.\venv\Scripts\activate.bat

# Instalar dependências
pip install -r requirements.txt
```

## Erro de CORS no navegador

**Verificar:**
1. O adapter está rodando em `http://localhost:8000`?
2. O frontend está em `http://localhost:3000`?
3. Os CORS no adapter estão configurados corretamente?

**Solução:**
Verifique o arquivo `frontend/adapter/app.py` - as origens permitidas devem incluir `http://localhost:3000`.

## Erro: "Arquivo não encontrado" ao salvar regras

**Solução:**
1. Verifique se o arquivo `Regras_Comissoes.xlsx` existe na pasta raiz do robô
2. Verifique se `ROBO_ROOT_PATH` no `.env` está correto:
```powershell
cd frontend\adapter
# Editar .env e verificar ROBO_ROOT_PATH
```

## Erro: Porta 8000 já em uso

**Solução 1: Usar outra porta**
```powershell
uvicorn app:app --reload --port 8001
```
E atualizar `frontend/src/services/api.js`:
```javascript
const API_BASE_URL = 'http://localhost:8001';
```

**Solução 2: Encerrar processo na porta 8000**
```powershell
# Encontrar processo
netstat -ano | findstr :8000

# Matar processo (substitua PID pelo número encontrado)
taskkill /PID <PID> /F
```

## Erro ao fazer upload de arquivos

**Verificar:**
1. Tamanho do arquivo não excede limites
2. Formato correto (.xlsx, .xls, .csv conforme esperado)
3. Permissões de escrita na pasta raiz do robô

**Solução:**
- Verifique logs do adapter no terminal
- Verifique permissões da pasta `ROBO_ROOT_PATH`

## Progresso não atualiza

**Verificar:**
1. O robô Python está escrevendo `progress.json`?
2. O polling está funcionando? (verificar console do navegador)

**Solução:**
- Verificar se o arquivo `progress.json` está sendo criado na pasta raiz
- Verificar logs do adapter para erros

## Problemas de Política de Execução (PowerShell)

Se você receber erro sobre política de execução:

```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

Ou executar scripts diretamente:
```powershell
powershell -ExecutionPolicy Bypass -File .\run.ps1
```

