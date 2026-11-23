@echo off
setlocal
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" (
  echo Create the environment first: py -3.11 -m venv .venv
  pause
  exit /b 1
)
if not exist "config.yaml" copy /y "config.example.yaml" "config.yaml" >nul
".venv\Scripts\python.exe" -m app.main
set "app_exit_code=%errorlevel%"
if not "%app_exit_code%"=="0" (
  echo Dota SEA Translator exited with code %app_exit_code%. See the error above.
  pause
)
exit /b %app_exit_code%

