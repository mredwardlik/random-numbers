@echo off
rem Builds random-numbers.exe into the dist folder
if not exist .env\Scripts\activate.bat python -m venv .env
call .env\Scripts\activate.bat
pip install . pyinstaller
pyinstaller --onefile --noconfirm --name random-numbers --icon icon.ico main.py
echo.
echo Done: dist\random-numbers.exe
pause
