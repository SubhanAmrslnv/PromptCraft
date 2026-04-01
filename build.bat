@echo off
echo Installing dependencies...
pip install -r requirements.txt

echo.
echo Building PromptCraft.exe...
pyinstaller --onefile --console --name PromptCraft chat.py

echo.
echo Done. Your executable is at:
echo   dist\PromptCraft.exe
echo.
echo Set your API key before running:
echo   set ANTHROPIC_API_KEY=sk-ant-...
echo   dist\PromptCraft.exe
pause
