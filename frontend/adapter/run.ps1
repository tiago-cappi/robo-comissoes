# Script PowerShell para iniciar o adapter

Write-Host "Iniciando adapter FastAPI..." -ForegroundColor Green
Write-Host ""

# Verificar se existe arquivo .env
if (-not (Test-Path .env)) {
    Write-Host "AVISO: Arquivo .env não encontrado!" -ForegroundColor Yellow
    Write-Host "Criando .env a partir do exemplo..." -ForegroundColor Yellow
    Copy-Item .env.example .env
    Write-Host "Por favor, edite o arquivo .env e configure ROBO_ROOT_PATH" -ForegroundColor Yellow
    pause
    exit 1
}

# Verificar se venv existe
if (Test-Path venv\Scripts\Activate.ps1) {
    Write-Host "Ativando ambiente virtual..." -ForegroundColor Cyan
    & .\venv\Scripts\Activate.ps1
}

# Verificar se Python está disponível
try {
    $pythonVersion = python --version 2>&1
    Write-Host "Python encontrado: $pythonVersion" -ForegroundColor Cyan
} catch {
    Write-Host "Erro: Python não encontrado!" -ForegroundColor Red
    Write-Host "Certifique-se de que Python está instalado e no PATH" -ForegroundColor Yellow
    pause
    exit 1
}

# Verificar se uvicorn está instalado
$uvicornFound = $false
try {
    $null = Get-Command uvicorn -ErrorAction Stop
    $uvicornFound = $true
} catch {
    # Tentar usar python -m uvicorn como fallback
    Write-Host "uvicorn não encontrado no PATH, usando python -m uvicorn..." -ForegroundColor Yellow
}

# Verificar se as dependências estão instaladas
try {
    python -c "import fastapi" 2>&1 | Out-Null
    if ($LASTEXITCODE -ne 0) {
        throw "FastAPI não encontrado"
    }
} catch {
    Write-Host "Erro: Dependências não instaladas!" -ForegroundColor Red
    Write-Host "Instalando dependências..." -ForegroundColor Yellow
    pip install -r requirements.txt
    if ($LASTEXITCODE -ne 0) {
        Write-Host "Erro ao instalar dependências!" -ForegroundColor Red
        pause
        exit 1
    }
}

# Iniciar servidor
Write-Host "Iniciando servidor em http://localhost:8000..." -ForegroundColor Green
if ($uvicornFound) {
    uvicorn app:app --reload --port 8000
} else {
    python -m uvicorn app:app --reload --port 8000
}

