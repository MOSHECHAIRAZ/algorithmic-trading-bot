@echo off
:: IBKR Gateway Auto-Login Utility
:: This script will start the IBKR Gateway and automatically log in using Windows command scripting.
:: It's a standalone solution that doesn't depend on Python libraries.

echo IBKR Gateway Auto-Login Utility
echo ---------------------------------------------------

REM Configuration
set IBKR_PATH=C:\Jts\ibgateway\1037\ibgateway.exe
set IBKR_USER=bvqcpy485
set IBKR_PASS=R0533124116

REM Check if Gateway exists
if not exist "%IBKR_PATH%" (
    echo Error: Gateway not found at %IBKR_PATH%
    exit /b 1
)

REM Create temp VBS script for auto-login
echo Creating auto-login script...
echo WScript.Sleep 4000 > ibkr_login.vbs
echo Set WshShell = WScript.CreateObject("WScript.Shell") >> ibkr_login.vbs
echo WshShell.AppActivate "IB Gateway" >> ibkr_login.vbs
echo WScript.Sleep 500 >> ibkr_login.vbs
echo WshShell.SendKeys "%IBKR_USER%" >> ibkr_login.vbs
echo WshShell.SendKeys "{TAB}" >> ibkr_login.vbs
echo WScript.Sleep 200 >> ibkr_login.vbs
echo WshShell.SendKeys "%IBKR_PASS%" >> ibkr_login.vbs
echo WScript.Sleep 200 >> ibkr_login.vbs
echo WshShell.SendKeys "{ENTER}" >> ibkr_login.vbs

REM Start Gateway
echo Starting IBKR Gateway...
start "" "%IBKR_PATH%"

REM Wait a bit then run the VBS script
timeout /t 1 /nobreak > nul
echo Running auto-login script...
start /min wscript.exe ibkr_login.vbs

echo Login attempt complete. The Gateway should be starting up now.
echo If login was unsuccessful, you may need to log in manually.

REM Cleanup
timeout /t 10 /nobreak > nul
del ibkr_login.vbs
