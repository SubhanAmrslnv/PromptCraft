@echo off
echo Installing dependencies...
pip install -r requirements.txt

echo.
echo Building PromptCraft.exe...
python -m PyInstaller --onefile --console --name PromptCraft --distpath . --workpath build\tmp --specpath build --collect-data pyfiglet chat.py

echo.
echo Cleaning up build artifacts...
rmdir /s /q build

echo.
echo Build complete. Launching PromptCraft...
start "" "PromptCraft.exe"
