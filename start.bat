@echo off
cd /d %~dp0
if not exist venv (
    python -m venv venv
    venv\Scripts\activate.bat
    pip install -r requirements.txt
    python -m pip install --upgrade pip
    python main.py
) else (
    venv\Scripts\activate.bat
    python main.py
)