@echo off
chcp 65001 > nul
echo ארגון הפרויקט...
echo.

cd /d "%~dp0.."
python scripts\organize_project.py

echo.
pause
