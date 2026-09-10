@echo off
echo === Installation de PyInstaller ===
pip install pyinstaller >nul

echo.
echo === Construction de l'executable ===
pyinstaller --onefile --windowed --name "NeuralGameFixer" --icon=icon.ico --collect-all customtkinter main.py

echo.
echo === Copie de la base de bugs et de l'icone a cote de l'executable ===
copy /Y bugs_data.json dist\bugs_data.json
copy /Y icon.ico dist\icon.ico

echo.
echo Termine ! L'executable se trouve dans dist\NeuralGameFixer.exe
pause
