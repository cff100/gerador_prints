@echo off
setlocal
cd /d "%~dp0"

if exist ".venv\Scripts\pythonw.exe" (
    start "" ".venv\Scripts\pythonw.exe" "run.py"
) else if exist ".venv\Scripts\python.exe" (
    start "" ".venv\Scripts\python.exe" "run.py"
) else (
    echo [ERRO] Ambiente virtual (.venv) nao encontrado!
    echo.
    echo Para configurar pela primeira vez:
    echo   1. python -m venv .venv
    echo   2. .\.venv\Scripts\pip install -r requirements.txt
    echo.
    pause
)
