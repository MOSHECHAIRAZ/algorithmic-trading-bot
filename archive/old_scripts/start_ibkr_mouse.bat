@echo off
:: IBKR Gateway Mouse-Click Solution with Direct Mouse Control
:: This script uses a more direct approach with mouse clicks

echo IBKR Gateway Direct Mouse Click Login
echo ---------------------------------------------------

REM Start Gateway
echo Starting IBKR Gateway...
start "" "C:\Jts\ibgateway\1037\ibgateway.exe"

REM Wait for Gateway to initialize
echo Waiting for Gateway to fully initialize (15 seconds)...
timeout /t 15 /nobreak > nul

REM Create AutoHotkey script - a more powerful automation tool
echo Creating AutoHotkey script...
echo #NoEnv > ibkr_login.ahk
echo SetWorkingDir %A_ScriptDir% >> ibkr_login.ahk
echo SendMode Input >> ibkr_login.ahk
echo SetTitleMatchMode, 2 >> ibkr_login.ahk

REM Attempt to activate the window
echo WinActivate, IB Gateway >> ibkr_login.ahk
echo Sleep, 1000 >> ibkr_login.ahk
echo WinActivate, Interactive Brokers >> ibkr_login.ahk
echo Sleep, 1000 >> ibkr_login.ahk

REM Click on various potential username field positions and input
echo Loop, 6 { >> ibkr_login.ahk
echo   xPos := 300 + (A_Index-1)*50 >> ibkr_login.ahk
echo   yPos := 250 + (A_Index-1)*30 >> ibkr_login.ahk
echo   MouseClick, left, %xPos%, %yPos% >> ibkr_login.ahk
echo   Sleep, 300 >> ibkr_login.ahk
echo   Send, ^a >> ibkr_login.ahk
echo   Sleep, 200 >> ibkr_login.ahk
echo   Send, {Delete} >> ibkr_login.ahk
echo   Sleep, 200 >> ibkr_login.ahk
echo   Send, bvqcpy485 >> ibkr_login.ahk
echo   Sleep, 500 >> ibkr_login.ahk
echo } >> ibkr_login.ahk

REM Press Tab to move to password field
echo Send, {Tab} >> ibkr_login.ahk
echo Sleep, 1000 >> ibkr_login.ahk

REM Clear and enter password
echo Send, ^a >> ibkr_login.ahk
echo Sleep, 200 >> ibkr_login.ahk
echo Send, {Delete} >> ibkr_login.ahk
echo Sleep, 200 >> ibkr_login.ahk
echo Send, R0533124116 >> ibkr_login.ahk
echo Sleep, 500 >> ibkr_login.ahk

REM Press Enter to login
echo Send, {Enter} >> ibkr_login.ahk

REM Check if AutoHotkey is installed
where /q autohotkey.exe
if %ERRORLEVEL% == 0 (
    echo AutoHotkey is installed, running script...
    start "" autohotkey.exe ibkr_login.ahk
) else (
    echo AutoHotkey not found. To use this script, please install AutoHotkey from https://www.autohotkey.com/
    echo For now, we'll try a VBScript alternative...
    
    REM Create a basic VBScript as fallback
    echo Set WshShell = WScript.CreateObject("WScript.Shell") > ibkr_login.vbs
    echo WScript.Sleep 1000 >> ibkr_login.vbs
    
    REM Try to find the window
    echo On Error Resume Next >> ibkr_login.vbs
    echo WshShell.AppActivate "IB Gateway" >> ibkr_login.vbs
    echo If Err.Number ^<^> 0 Then >> ibkr_login.vbs
    echo     WshShell.AppActivate "Interactive Brokers" >> ibkr_login.vbs
    echo End If >> ibkr_login.vbs
    echo On Error Goto 0 >> ibkr_login.vbs
    
    REM Slow character by character typing for username
    echo WScript.Sleep 1000 >> ibkr_login.vbs
    echo WshShell.SendKeys "b" >> ibkr_login.vbs
    echo WScript.Sleep 100 >> ibkr_login.vbs
    echo WshShell.SendKeys "v" >> ibkr_login.vbs
    echo WScript.Sleep 100 >> ibkr_login.vbs
    echo WshShell.SendKeys "q" >> ibkr_login.vbs
    echo WScript.Sleep 100 >> ibkr_login.vbs
    echo WshShell.SendKeys "c" >> ibkr_login.vbs
    echo WScript.Sleep 100 >> ibkr_login.vbs
    echo WshShell.SendKeys "p" >> ibkr_login.vbs
    echo WScript.Sleep 100 >> ibkr_login.vbs
    echo WshShell.SendKeys "y" >> ibkr_login.vbs
    echo WScript.Sleep 100 >> ibkr_login.vbs
    echo WshShell.SendKeys "4" >> ibkr_login.vbs
    echo WScript.Sleep 100 >> ibkr_login.vbs
    echo WshShell.SendKeys "8" >> ibkr_login.vbs
    echo WScript.Sleep 100 >> ibkr_login.vbs
    echo WshShell.SendKeys "5" >> ibkr_login.vbs
    echo WScript.Sleep 500 >> ibkr_login.vbs
    
    REM Tab to password field
    echo WshShell.SendKeys "{TAB}" >> ibkr_login.vbs
    echo WScript.Sleep 1000 >> ibkr_login.vbs
    
    REM Type password character by character
    echo WshShell.SendKeys "R" >> ibkr_login.vbs
    echo WScript.Sleep 100 >> ibkr_login.vbs
    echo WshShell.SendKeys "0" >> ibkr_login.vbs
    echo WScript.Sleep 100 >> ibkr_login.vbs
    echo WshShell.SendKeys "5" >> ibkr_login.vbs
    echo WScript.Sleep 100 >> ibkr_login.vbs
    echo WshShell.SendKeys "3" >> ibkr_login.vbs
    echo WScript.Sleep 100 >> ibkr_login.vbs
    echo WshShell.SendKeys "3" >> ibkr_login.vbs
    echo WScript.Sleep 100 >> ibkr_login.vbs
    echo WshShell.SendKeys "1" >> ibkr_login.vbs
    echo WScript.Sleep 100 >> ibkr_login.vbs
    echo WshShell.SendKeys "2" >> ibkr_login.vbs
    echo WScript.Sleep 100 >> ibkr_login.vbs
    echo WshShell.SendKeys "4" >> ibkr_login.vbs
    echo WScript.Sleep 100 >> ibkr_login.vbs
    echo WshShell.SendKeys "1" >> ibkr_login.vbs
    echo WScript.Sleep 100 >> ibkr_login.vbs
    echo WshShell.SendKeys "1" >> ibkr_login.vbs
    echo WScript.Sleep 100 >> ibkr_login.vbs
    echo WshShell.SendKeys "6" >> ibkr_login.vbs
    echo WScript.Sleep 1000 >> ibkr_login.vbs
    
    REM Press Enter
    echo WshShell.SendKeys "{ENTER}" >> ibkr_login.vbs
    
    echo Running VBScript as fallback...
    cscript.exe ibkr_login.vbs
)

echo Login attempt complete.
echo Cleaning up...
timeout /t 3 /nobreak > nul
if exist ibkr_login.ahk del ibkr_login.ahk
if exist ibkr_login.vbs del ibkr_login.vbs
