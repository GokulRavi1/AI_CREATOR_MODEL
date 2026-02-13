@echo off
set "KOHYA_DIR=C:\Kohya_ss"  REM CHANGE THIS to your actual Kohya folder if different
set "VENV_DIR=%KOHYA_DIR%\venv"

if not exist "%KOHYA_DIR%" (
    echo [ERROR] Kohya directory not found at: %KOHYA_DIR%
    echo Please edit this script and set the correct KOHYA_DIR path.
    pause
    exit /b
)

echo Activate venv...
call "%VENV_DIR%\Scripts\activate.bat"

echo Starting training...
python "%KOHYA_DIR%\sd-scripts\train_network.py" %*

echo Training finished!
pause
