@echo off
setlocal enableextensions enabledelayedexpansion

echo Starting IB Gateway with Auto-Login...
echo.

:: Start IB Gateway directly
echo Opening IB Gateway...
start "" "C:\Jts\ibgateway\1037\ibgateway.exe"

:: Wait for the login window to appear
echo Waiting for login window to appear...
timeout /t 10

:: Use PowerShell to automate the login
echo Automating login...
powershell -Command "
Add-Type -AssemblyName System.Windows.Forms
Start-Sleep -Seconds 2

# Find the IB Gateway window
$windowTitle = '*Gateway*'
$processes = Get-Process | Where-Object { $_.MainWindowTitle -like $windowTitle }

if ($processes) {
    Write-Host 'Gateway window found, sending login credentials...'
    
    # Send username
    [System.Windows.Forms.SendKeys]::SendWait('bvqcpy485')
    Start-Sleep -Milliseconds 500
    
    # Tab to password field
    [System.Windows.Forms.SendKeys]::SendWait('{TAB}')
    Start-Sleep -Milliseconds 500
    
    # Send password
    [System.Windows.Forms.SendKeys]::SendWait('R0533124116')
    Start-Sleep -Milliseconds 500
    
    # Press Enter to login
    [System.Windows.Forms.SendKeys]::SendWait('{ENTER}')
    
    Write-Host 'Login credentials sent successfully!'
} else {
    Write-Host 'Gateway window not found. Please login manually.'
}
"

echo.
echo IB Gateway should now be starting with auto-login.
echo If login failed, please enter credentials manually.
echo.
pause
