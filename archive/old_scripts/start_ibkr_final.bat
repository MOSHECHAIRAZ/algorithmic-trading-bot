@echo off
:: IBKR Gateway Final Approach
:: This is a super-simple approach focusing only on timing and direct input

echo IBKR Final Approach Auto-Login
echo ---------------------------------------------------

REM Start Gateway
echo Starting IBKR Gateway...
start "" "C:\Jts\ibgateway\1037\ibgateway.exe"

REM Close any existing VBS script if it exists
if exist final_login.vbs del final_login.vbs

REM Wait longer for Gateway to initialize
echo Waiting for Gateway to fully initialize (15 seconds)...
timeout /t 15 /nobreak > nul

REM Try to bring all windows to front
echo Sending Win+D to show desktop...
powershell -Command "(New-Object -ComObject Shell.Application).MinimizeAll()"
timeout /t 2 /nobreak > nul
echo Restoring windows...
powershell -Command "(New-Object -ComObject Shell.Application).UndoMinimizeAll()"
timeout /t 2 /nobreak > nul

REM Create very basic VBS script
echo Set WshShell = WScript.CreateObject("WScript.Shell") > final_login.vbs
echo WScript.Echo "Starting login sequence..." >> final_login.vbs

REM Try Alt+Tab multiple times with longer wait time
for /l %%i in (1, 1, 5) do (
    echo WshShell.SendKeys "%%{TAB}" >> final_login.vbs
    echo WScript.Sleep 500 >> final_login.vbs
)

REM Wait longer before starting input
echo WScript.Sleep 2000 >> final_login.vbs

REM Try to click in the form - use SendKeys "{CLICK}" if on newer VBScript
echo WScript.Echo "Attempting to click on form..." >> final_login.vbs
echo ' Try to click on the form (center of the screen) >> final_login.vbs
echo Function ClickAt(x, y) >> final_login.vbs
echo   WshShell.Run "powershell -Command [Windows.Forms.Cursor]::Position = New-Object System.Drawing.Point(" ^& x ^& "," ^& y ^& "); [Runtime.InteropServices.Marshal]::GetLastWin32Error()", 0, True >> final_login.vbs
echo   WScript.Sleep 200 >> final_login.vbs
echo   WshShell.SendKeys "{CLICK}" >> final_login.vbs
echo   WScript.Sleep 200 >> final_login.vbs
echo End Function >> final_login.vbs
echo ' Try clicking at likely username field positions >> final_login.vbs
echo ClickAt 400, 300 >> final_login.vbs
echo WScript.Sleep 500 >> final_login.vbs

REM Clear field and handle input with focus on username field (character by character)
echo WScript.Echo "Clearing field with Ctrl+A and Delete..." >> final_login.vbs
echo WshShell.SendKeys "^a" >> final_login.vbs
echo WScript.Sleep 300 >> final_login.vbs
echo WshShell.SendKeys "{DELETE}" >> final_login.vbs
echo WScript.Sleep 300 >> final_login.vbs

REM Type username one character at a time
echo WScript.Echo "Typing username character by character..." >> final_login.vbs
echo WshShell.SendKeys "b" >> final_login.vbs
echo WScript.Sleep 100 >> final_login.vbs
echo WshShell.SendKeys "v" >> final_login.vbs
echo WScript.Sleep 100 >> final_login.vbs
echo WshShell.SendKeys "q" >> final_login.vbs
echo WScript.Sleep 100 >> final_login.vbs
echo WshShell.SendKeys "c" >> final_login.vbs
echo WScript.Sleep 100 >> final_login.vbs
echo WshShell.SendKeys "p" >> final_login.vbs
echo WScript.Sleep 100 >> final_login.vbs
echo WshShell.SendKeys "y" >> final_login.vbs
echo WScript.Sleep 100 >> final_login.vbs
echo WshShell.SendKeys "4" >> final_login.vbs
echo WScript.Sleep 100 >> final_login.vbs
echo WshShell.SendKeys "8" >> final_login.vbs
echo WScript.Sleep 100 >> final_login.vbs
echo WshShell.SendKeys "5" >> final_login.vbs
echo WScript.Sleep 500 >> final_login.vbs

REM Multiple Tab presses to ensure focus moves to password field
echo WScript.Echo "Pressing Tab multiple times to focus password field..." >> final_login.vbs
echo WshShell.SendKeys "{TAB}" >> final_login.vbs
echo WScript.Sleep 1000 >> final_login.vbs
echo WshShell.SendKeys "{TAB}" >> final_login.vbs
echo WScript.Sleep 1000 >> final_login.vbs

REM Clear password field
echo WScript.Echo "Clearing password field..." >> final_login.vbs
echo WshShell.SendKeys "^a" >> final_login.vbs
echo WScript.Sleep 300 >> final_login.vbs
echo WshShell.SendKeys "{DELETE}" >> final_login.vbs
echo WScript.Sleep 300 >> final_login.vbs

REM Type password one character at a time
echo WScript.Echo "Typing password character by character..." >> final_login.vbs
echo WshShell.SendKeys "R" >> final_login.vbs
echo WScript.Sleep 100 >> final_login.vbs
echo WshShell.SendKeys "0" >> final_login.vbs
echo WScript.Sleep 100 >> final_login.vbs
echo WshShell.SendKeys "5" >> final_login.vbs
echo WScript.Sleep 100 >> final_login.vbs
echo WshShell.SendKeys "3" >> final_login.vbs
echo WScript.Sleep 100 >> final_login.vbs
echo WshShell.SendKeys "3" >> final_login.vbs
echo WScript.Sleep 100 >> final_login.vbs
echo WshShell.SendKeys "1" >> final_login.vbs
echo WScript.Sleep 100 >> final_login.vbs
echo WshShell.SendKeys "2" >> final_login.vbs
echo WScript.Sleep 100 >> final_login.vbs
echo WshShell.SendKeys "4" >> final_login.vbs
echo WScript.Sleep 100 >> final_login.vbs
echo WshShell.SendKeys "1" >> final_login.vbs
echo WScript.Sleep 100 >> final_login.vbs
echo WshShell.SendKeys "1" >> final_login.vbs
echo WScript.Sleep 100 >> final_login.vbs
echo WshShell.SendKeys "6" >> final_login.vbs
echo WScript.Sleep 1000 >> final_login.vbs
echo WshShell.SendKeys "{ENTER}" >> final_login.vbs

echo Running final login script...
cscript.exe final_login.vbs

echo Login attempt complete.
echo Cleaning up...
timeout /t 3 /nobreak > nul
del final_login.vbs
