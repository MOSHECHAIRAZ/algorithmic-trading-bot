@echo off
:: IBKR Gateway Simple Auto-Login Utility (Bare Minimum Approach)
:: This script uses the most direct approach possible

echo IBKR Gateway Simple Auto-Login Utility
echo ---------------------------------------------------

REM Configuration
set IBKR_PATH=C:\Jts\ibgateway\1037\ibgateway.exe
set IBKR_USER=bvqcpy485
set IBKR_PASS=R0533124116

REM Create minimal VBS script
echo Creating minimal auto-login script...
echo Set WshShell = WScript.CreateObject("WScript.Shell") > ibkr_login_simple.vbs
echo WScript.Sleep 8000 >> ibkr_login_simple.vbs

REM Cycle through applications
echo For i = 1 to 8 >> ibkr_login_simple.vbs
echo   WshShell.SendKeys "%%{TAB}" >> ibkr_login_simple.vbs
echo   WScript.Sleep 700 >> ibkr_login_simple.vbs
echo Next >> ibkr_login_simple.vbs

REM Enter credentials directly (no environment variables)
echo WshShell.SendKeys "bvqcpy485" >> ibkr_login_simple.vbs
echo WScript.Sleep 1000 >> ibkr_login_simple.vbs
echo WshShell.SendKeys "{TAB}" >> ibkr_login_simple.vbs
echo WScript.Sleep 1000 >> ibkr_login_simple.vbs
echo WshShell.SendKeys "R0533124116" >> ibkr_login_simple.vbs
echo WScript.Sleep 1000 >> ibkr_login_simple.vbs
echo WshShell.SendKeys "{ENTER}" >> ibkr_login_simple.vbs

REM Start Gateway
echo Starting IBKR Gateway...
start "" "%IBKR_PATH%"

REM Wait and then run the simple VBS script
echo Waiting for Gateway to initialize (8 seconds)...
timeout /t 8 /nobreak > nul
echo Running minimal auto-login script...
cscript.exe ibkr_login_simple.vbs

echo Login attempt in progress. The Gateway should be logging in now.
echo If this minimal approach doesn't work, try the enhanced version.

REM Clean up
timeout /t 5 /nobreak > nul
del ibkr_login_simple.vbs
