# Correções Imediatas

## Problema 1: "uvicorn não é reconhecido"

**Solução rápida:**
```powershell
cd frontend\adapter
python -m uvicorn app:app --reload --port 8000
```

Ou use o script que já foi corrigido:
```powershell
cd frontend\adapter
.\run.ps1
```

O script agora detecta automaticamente se `uvicorn` está no PATH e usa `python -m uvicorn` como fallback.

## Problema 2: Erro do React "allowedHosts[0] should be a non-empty string"

**Solução rápida:**

1. **Instalar nova dependência:**
```powershell
cd frontend
npm install http-proxy-middleware
```

2. **Criar arquivo `.env` na pasta frontend:**
```powershell
# Criar arquivo .env
echo REACT_APP_API_URL=http://localhost:8000 > .env
echo DANGEROUSLY_DISABLE_HOST_CHECK=true >> .env
```

Ou criar manualmente o arquivo `frontend/.env` com:
```
REACT_APP_API_URL=http://localhost:8000
DANGEROUSLY_DISABLE_HOST_CHECK=true
```

3. **Reiniciar o servidor React:**
```powershell
# Parar o servidor atual (Ctrl+C)
# Depois:
npm start
```

## Verificação Rápida

**Terminal 1 (Adapter):**
```powershell
cd frontend\adapter
python -m uvicorn app:app --reload --port 8000
```
Deve mostrar: `Application startup complete` e `Uvicorn running on http://127.0.0.1:8000`

**Terminal 2 (Frontend):**
```powershell
cd frontend
npm install  # se ainda não instalou http-proxy-middleware
npm start
```
Deve abrir automaticamente em `http://localhost:3000`

## Se ainda houver problemas

Consulte `SOLUCAO_PROBLEMAS.md` para mais detalhes.

