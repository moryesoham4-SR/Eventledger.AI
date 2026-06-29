@echo off
echo ========================================
echo   EventLedger AI - Starting...
echo ========================================
echo.

:: Install/upgrade pip and streamlit
echo Installing dependencies...
python -m pip install --upgrade pip --quiet
python -m pip install streamlit plotly pandas numpy sqlalchemy reportlab openpyxl scikit-learn bcrypt --quiet

echo.
echo Starting EventLedger AI...
echo Browser will open at: http://localhost:8501
echo Press Ctrl+C to stop.
echo.

:: Run streamlit using python -m (always works even if PATH is broken)
python -m streamlit run app.py --server.port 8501

pause
