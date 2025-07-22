@echo off
:: IBKR Gateway Final Ultra-Simple Solution
:: The simplest approach with character-by-character typing

echo IBKR Gateway Ultra-Simple Login
echo ---------------------------------------------------

REM Start Gateway
echo Starting IBKR Gateway...
start "" "C:\Jts\ibgateway\1037\ibgateway.exe"

REM Wait for Gateway to initialize
echo Waiting for Gateway to fully initialize (15 seconds)...
timeout /t 15 /nobreak > nul

REM Create simple VBScript with careful quoting and structure
echo Set WshShell = CreateObject("WScript.Shell") > login.vbs
echo WScript.Sleep 1000 >> login.vbs

REM Try to find the window with various titles
echo WshShell.AppActivate "IB Gateway" >> login.vbs
echo WScript.Sleep 1000 >> login.vbs

REM Try Alt+Tab multiple times
echo For i = 1 to 5 >> login.vbs
echo   WshShell.SendKeys "%%{TAB}" >> login.vbs
echo   WScript.Sleep 500 >> login.vbs
echo Next >> login.vbs

REM Type username character by character
echo WScript.Sleep 1000 >> login.vbs
echo WshShell.SendKeys "b" >> login.vbs
echo WScript.Sleep 50 >> login.vbs
echo WshShell.SendKeys "v" >> login.vbs
echo WScript.Sleep 50 >> login.vbs
echo WshShell.SendKeys "q" >> login.vbs
echo WScript.Sleep 50 >> login.vbs
echo WshShell.SendKeys "c" >> login.vbs
echo WScript.Sleep 50 >> login.vbs
echo WshShell.SendKeys "p" >> login.vbs
echo WScript.Sleep 50 >> login.vbs
echo WshShell.SendKeys "y" >> login.vbs
echo WScript.Sleep 50 >> login.vbs
echo WshShell.SendKeys "4" >> login.vbs
echo WScript.Sleep 50 >> login.vbs
echo WshShell.SendKeys "8" >> login.vbs
echo WScript.Sleep 50 >> login.vbs
echo WshShell.SendKeys "5" >> login.vbs
echo WScript.Sleep 500 >> login.vbs

REM Tab to password field - try multiple times
echo WshShell.SendKeys "{TAB}" >> login.vbs
echo WScript.Sleep 500 >> login.vbs
echo WshShell.SendKeys "{TAB}" >> login.vbs
echo WScript.Sleep 500 >> login.vbs

REM Type password character by character
echo WshShell.SendKeys "R" >> login.vbs
echo WScript.Sleep 50 >> login.vbs
echo WshShell.SendKeys "0" >> login.vbs
echo WScript.Sleep 50 >> login.vbs
echo WshShell.SendKeys "5" >> login.vbs
echo WScript.Sleep 50 >> login.vbs
echo WshShell.SendKeys "3" >> login.vbs
echo WScript.Sleep 50 >> login.vbs
echo WshShell.SendKeys "3" >> login.vbs
echo WScript.Sleep 50 >> login.vbs
echo WshShell.SendKeys "1" >> login.vbs
echo WScript.Sleep 50 >> login.vbs
echo WshShell.SendKeys "2" >> login.vbs
echo WScript.Sleep 50 >> login.vbs
echo WshShell.SendKeys "4" >> login.vbs
echo WScript.Sleep 50 >> login.vbs
echo WshShell.SendKeys "1" >> login.vbs
echo WScript.Sleep 50 >> login.vbs
echo WshShell.SendKeys "1" >> login.vbs
echo WScript.Sleep 50 >> login.vbs
echo WshShell.SendKeys "6" >> login.vbs
echo WScript.Sleep 500 >> login.vbs

REM Press Enter
echo WshShell.SendKeys "{ENTER}" >> login.vbs

echo Running login script...
cscript.exe login.vbs

echo Login attempt complete.
timeout /t 3 /nobreak > nul
del login.vbs
