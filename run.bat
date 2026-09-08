@echo off
setlocal
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" (
  echo Create the environment first: py -3.11 -m venv .venv
  exit /b 1
)
if not exist "config.yaml" copy /y "config.example.yaml" "config.yaml" >nul
".venv\Scripts\python.exe" -m app.main

