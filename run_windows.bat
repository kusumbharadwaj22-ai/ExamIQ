@echo off
cd /d "%~dp0"
where g++ >nul 2>nul
if %errorlevel%==0 (
  g++ cpp\analytics.cpp -o analytics.exe -std=c++17
)
python -m pip install -r requirements.txt
python app.py
pause
