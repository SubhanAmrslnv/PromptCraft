@echo off
echo Installing dependencies...
pip install -r requirements.txt

echo.
echo Building PromptCraft.exe...
python -m PyInstaller --onefile --windowed --name PromptCraft --distpath . --workpath build\tmp --specpath build --icon "%~dp0app.ico" chat.py

echo.
echo Cleaning up build artifacts...
rmdir /s /q build

echo.
echo Build complete. Launching PromptCraft...
start "" "PromptCraft.exe"
