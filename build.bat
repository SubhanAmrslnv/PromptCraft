@echo off
echo Installing dependencies...
pip install -r requirements.txt

echo.
echo Building PromptCraft.exe...
pyinstaller --onefile --console --name PromptCraft chat.py

echo.
echo Build complete. Launching PromptCraft...
start "" "dist\PromptCraft.exe"
