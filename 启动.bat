@echo off
chcp 65001 >nul
cd /d "%~dp0"
set PYTHONUTF8=1
if not exist ".venv\Scripts\python.exe" (
  echo [ERROR] .venv not found. Please redeploy the project.
  pause
  exit /b 1
)
rem 无参数时：双击启动 = 环境自检 + 一键演示；有参数时：原样转发给 main.py
if "%~1"=="" (
  ".venv\Scripts\python.exe" "main.py" check
  ".venv\Scripts\python.exe" "main.py" demo
) else (
  ".venv\Scripts\python.exe" "main.py" %*
)
echo.
pause
