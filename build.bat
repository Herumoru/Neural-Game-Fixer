@echo off
echo === Installation de PyInstaller ===
pip install pyinstaller >nul

echo.
echo === Construction de l'executable ===
pyinstaller --onefile --windowed --name "NeuralGameFixer" --collect-all customtkinter main.py

echo.
echo === Copie de la base de bugs a cote de l'executable ===
copy /Y bugs_data.json dist\bugs_data.json

echo.
echo Termine ! L'executable se trouve dans dist\NeuralGameFixer.exe
pause
