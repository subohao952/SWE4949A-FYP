@echo off
chcp 65001 >nul
setlocal

cd /d "%~dp0"

echo [1/4] Checking Python...
python --version >nul 2>&1
if errorlevel 1 (
  echo Python not found. Install Python 3.10+ first.
  pause
  exit /b 1
)

echo [2/4] Installing dependencies...
python -m pip install -r requirements.txt
if errorlevel 1 (
  echo Dependency install failed.
  pause
  exit /b 1
)

echo [3/4] Configuring local free LLM mode...
set LLM_PROVIDER=local
set OLLAMA_MODEL=qwen2.5:7b-instruct
set OLLAMA_BASE_URL=http://127.0.0.1:11434

echo [4/4] Starting app in local mode...
echo Make sure Ollama is installed and running.
echo If model is missing, run: ollama pull qwen2.5:7b-instruct
start "" "http://127.0.0.1:8000"
python -m uvicorn app.main:app --reload

pause
