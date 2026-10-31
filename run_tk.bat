@echo off
cd /d "%~dp0"
g++ cpp\analytics.cpp -o analytics.exe -std=c++17
python tk_app.py
pause
