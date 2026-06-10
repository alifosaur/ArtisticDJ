@echo off
cd /d "%~dp0"
echo Clearing old cached code...
if exist __pycache__ rmdir /s /q __pycache__
echo Starting Aura Canvas...
aura_env\Scripts\python.exe main.py
pause
