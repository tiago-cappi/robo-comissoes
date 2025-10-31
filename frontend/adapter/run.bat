@echo off
echo Iniciando adapter FastAPI...
echo.

REM Verificar se existe arquivo .env
if not exist .env (
    echo AVISO: Arquivo .env não encontrado!
    echo Criando .env a partir do exemplo...
    copy .env.example .env
    echo Por favor, edite o arquivo .env e configure ROBO_ROOT_PATH
    pause
    exit /b 1
)

REM Ativar ambiente virtual se existir
if exist venv\Scripts\activate.bat (
    call venv\Scripts\activate.bat
)

REM Verificar se uvicorn está no PATH
where uvicorn >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    echo Usando uvicorn do PATH...
    uvicorn app:app --reload --port 8000
) else (
    echo uvicorn não encontrado no PATH, usando python -m uvicorn...
    python -m uvicorn app:app --reload --port 8000
)

pause

