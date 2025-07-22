@echo off
:: IBKR Gateway Enhanced Auto-Login Utility
:: This script will start the IBKR Gateway and automatically log in using advanced VBScript

echo IBKR Gateway Enhanced Auto-Login Utility
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

REM Create enhanced VBS script for auto-login
echo Creating enhanced auto-login script...
echo ' IBKR Gateway Auto-Login Script > ibkr_login.vbs
echo ' Created for automated login >> ibkr_login.vbs
echo. >> ibkr_login.vbs
echo ' Wait longer for the Gateway window to appear >> ibkr_login.vbs
echo WScript.Echo "Waiting for IBKR Gateway window to appear..." >> ibkr_login.vbs
echo WScript.Sleep 8000 >> ibkr_login.vbs
echo Set WshShell = WScript.CreateObject("WScript.Shell") >> ibkr_login.vbs

echo ' Show desktop first (Win+D) then Alt+Tab to bring gateway window to front >> ibkr_login.vbs
echo WshShell.SendKeys "^{ESC}" >> ibkr_login.vbs
echo WScript.Sleep 500 >> ibkr_login.vbs
echo WshShell.SendKeys "d" >> ibkr_login.vbs
echo WScript.Sleep 1000 >> ibkr_login.vbs
echo WshShell.SendKeys "%%{TAB}" >> ibkr_login.vbs
echo WScript.Sleep 1000 >> ibkr_login.vbs

echo ' Try different possible window titles >> ibkr_login.vbs
echo Dim WindowFound >> ibkr_login.vbs
echo WindowFound = False >> ibkr_login.vbs
echo. >> ibkr_login.vbs

echo ' Try multiple window titles >> ibkr_login.vbs
echo Dim WindowTitles >> ibkr_login.vbs
echo WindowTitles = Array("IB Gateway", "Interactive Brokers Gateway", "IBKR Gateway Login", "Login", "Gateway") >> ibkr_login.vbs
echo. >> ibkr_login.vbs

echo For Each title In WindowTitles >> ibkr_login.vbs
echo   If Not WindowFound Then >> ibkr_login.vbs
echo     On Error Resume Next >> ibkr_login.vbs
echo     WshShell.AppActivate title >> ibkr_login.vbs
echo     If Err.Number = 0 Then >> ibkr_login.vbs
echo       WindowFound = True >> ibkr_login.vbs
echo       WScript.Echo "Found window: " ^& title >> ibkr_login.vbs
echo     End If >> ibkr_login.vbs
echo     On Error Goto 0 >> ibkr_login.vbs
echo   End If >> ibkr_login.vbs
echo Next >> ibkr_login.vbs
echo. >> ibkr_login.vbs

echo If Not WindowFound Then >> ibkr_login.vbs
echo   WScript.Echo "Window not found, trying desktop method..." >> ibkr_login.vbs
echo   ' Click on desktop and then Alt+Tab to get to the last active window >> ibkr_login.vbs
echo   WshShell.SendKeys "^{ESC}" >> ibkr_login.vbs
echo   WScript.Sleep 500 >> ibkr_login.vbs
echo   WshShell.SendKeys "d" >> ibkr_login.vbs
echo   WScript.Sleep 1000 >> ibkr_login.vbs
echo   ' Alt+Tab multiple times to find the window >> ibkr_login.vbs
echo   For i = 1 to 5 >> ibkr_login.vbs
echo     WshShell.SendKeys "%%{TAB}" >> ibkr_login.vbs
echo     WScript.Sleep 800 >> ibkr_login.vbs
echo   Next >> ibkr_login.vbs
echo End If >> ibkr_login.vbs
echo. >> ibkr_login.vbs

echo ' Force focus one more time >> ibkr_login.vbs
echo WshShell.SendKeys "%%{TAB}" >> ibkr_login.vbs
echo WScript.Sleep 1000 >> ibkr_login.vbs

echo ' Explicitly enter USERNAME directly (not using environment variable) >> ibkr_login.vbs
echo WshShell.SendKeys "^a" >> ibkr_login.vbs  
echo WScript.Sleep 300 >> ibkr_login.vbs
echo WshShell.SendKeys "{DELETE}" >> ibkr_login.vbs
echo WScript.Sleep 300 >> ibkr_login.vbs
echo WshShell.SendKeys "bvqcpy485" >> ibkr_login.vbs
echo WScript.Sleep 1000 >> ibkr_login.vbs

echo ' Explicitly tab to password field >> ibkr_login.vbs
echo WshShell.SendKeys "{TAB}" >> ibkr_login.vbs
echo WScript.Sleep 1000 >> ibkr_login.vbs

echo ' Explicitly enter PASSWORD directly >> ibkr_login.vbs
echo WshShell.SendKeys "^a" >> ibkr_login.vbs
echo WScript.Sleep 300 >> ibkr_login.vbs
echo WshShell.SendKeys "{DELETE}" >> ibkr_login.vbs
echo WScript.Sleep 300 >> ibkr_login.vbs
echo WshShell.SendKeys "R0533124116" >> ibkr_login.vbs
echo WScript.Sleep 1000 >> ibkr_login.vbs
echo WshShell.SendKeys "{ENTER}" >> ibkr_login.vbs
echo. >> ibkr_login.vbs

echo ' Handle potential additional prompts >> ibkr_login.vbs
echo WScript.Sleep 3000 >> ibkr_login.vbs
echo WshShell.SendKeys "{ENTER}" >> ibkr_login.vbs

echo ' Add one more attempt after a longer wait - sometimes the first attempt fails >> ibkr_login.vbs
echo WScript.Sleep 5000 >> ibkr_login.vbs
echo WScript.Echo "Trying one more time with the login fields..." >> ibkr_login.vbs

echo ' Try to find the window again >> ibkr_login.vbs
echo WindowFound = False >> ibkr_login.vbs
echo For Each title In WindowTitles >> ibkr_login.vbs
echo   If Not WindowFound Then >> ibkr_login.vbs
echo     On Error Resume Next >> ibkr_login.vbs
echo     WshShell.AppActivate title >> ibkr_login.vbs
echo     If Err.Number = 0 Then >> ibkr_login.vbs
echo       WindowFound = True >> ibkr_login.vbs
echo       WScript.Echo "Found window again: " ^& title >> ibkr_login.vbs
echo     End If >> ibkr_login.vbs
echo     On Error Goto 0 >> ibkr_login.vbs
echo   End If >> ibkr_login.vbs
echo Next >> ibkr_login.vbs

echo ' Force focus with Alt+Tab again >> ibkr_login.vbs
echo WshShell.SendKeys "%%{TAB}" >> ibkr_login.vbs
echo WScript.Sleep 1000 >> ibkr_login.vbs

echo ' Final attempt to input username >> ibkr_login.vbs
echo WshShell.SendKeys "^a" >> ibkr_login.vbs  
echo WScript.Sleep 300 >> ibkr_login.vbs
echo WshShell.SendKeys "{DELETE}" >> ibkr_login.vbs
echo WScript.Sleep 300 >> ibkr_login.vbs
echo WshShell.SendKeys "bvqcpy485" >> ibkr_login.vbs
echo WScript.Sleep 1000 >> ibkr_login.vbs
echo WshShell.SendKeys "{TAB}" >> ibkr_login.vbs
echo WScript.Sleep 1000 >> ibkr_login.vbs
echo WshShell.SendKeys "^a" >> ibkr_login.vbs
echo WScript.Sleep 300 >> ibkr_login.vbs
echo WshShell.SendKeys "{DELETE}" >> ibkr_login.vbs
echo WScript.Sleep 300 >> ibkr_login.vbs
echo WshShell.SendKeys "R0533124116" >> ibkr_login.vbs
echo WScript.Sleep 1000 >> ibkr_login.vbs
echo WshShell.SendKeys "{ENTER}" >> ibkr_login.vbs

REM Start Gateway
echo Starting IBKR Gateway...
start "" "%IBKR_PATH%"

REM Wait longer and then run the VBS script
echo Waiting for Gateway to initialize (5 seconds)...
timeout /t 5 /nobreak > nul
echo Running enhanced auto-login script...
cscript.exe ibkr_login.vbs

echo Login attempt in progress. The Gateway should be logging in now.
echo If login was unsuccessful, you may need to log in manually.

REM Cleanup
timeout /t 15 /nobreak > nul
del ibkr_login.vbs
