@echo off
echo ========================================
echo   EventLedger AI - Setup
echo ========================================
echo.
echo Checking Python...
python --version
if errorlevel 1 (
    echo.
    echo ERROR: Python not found!
    echo Install from https://python.org
    echo During install: CHECK "Add Python to PATH"
    pause
    exit /b 1
)
echo.
echo Installing all packages...
python -m pip install --upgrade pip
python -m pip install streamlit plotly pandas numpy sqlalchemy reportlab openpyxl scikit-learn bcrypt
echo.
echo ========================================
echo   Done! Now double-click run.bat
echo ========================================
pause
