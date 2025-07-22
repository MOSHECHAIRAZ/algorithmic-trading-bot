@echo off
echo Starting IB Gateway with Advanced Auto-Login...

REM Path to IBGateway executable
set GW_PATH=C:\Jts\ibgateway\1037\ibgateway.exe

REM Launch IB Gateway
echo Launching IB Gateway...
start "" "%GW_PATH%"

REM Create PowerShell script for auto-login with retry capability
echo Creating login script with retry capability...
echo $username = 'ליאור21' > "%TEMP%\iblogin_advanced.ps1"
echo $password = 'Abcd1234' >> "%TEMP%\iblogin_advanced.ps1"
echo Add-Type -AssemblyName System.Windows.Forms >> "%TEMP%\iblogin_advanced.ps1"
echo Add-Type -AssemblyName System.Drawing >> "%TEMP%\iblogin_advanced.ps1"
echo function Attempt-Login { >> "%TEMP%\iblogin_advanced.ps1"
echo   Write-Host "Waiting for login screen to appear..." >> "%TEMP%\iblogin_advanced.ps1"
echo   Start-Sleep -Seconds 20 >> "%TEMP%\iblogin_advanced.ps1"
echo   Write-Host "Attempting to login..." >> "%TEMP%\iblogin_advanced.ps1"
echo   [System.Windows.Forms.SendKeys]::SendWait($username) >> "%TEMP%\iblogin_advanced.ps1"
echo   Start-Sleep -Seconds 1 >> "%TEMP%\iblogin_advanced.ps1"
echo   [System.Windows.Forms.SendKeys]::SendWait('{TAB}') >> "%TEMP%\iblogin_advanced.ps1"
echo   Start-Sleep -Seconds 1 >> "%TEMP%\iblogin_advanced.ps1"
echo   [System.Windows.Forms.SendKeys]::SendWait($password) >> "%TEMP%\iblogin_advanced.ps1"
echo   Start-Sleep -Seconds 1 >> "%TEMP%\iblogin_advanced.ps1"
echo   [System.Windows.Forms.SendKeys]::SendWait('{ENTER}') >> "%TEMP%\iblogin_advanced.ps1"
echo   Write-Host "Login attempted!" >> "%TEMP%\iblogin_advanced.ps1"
echo } >> "%TEMP%\iblogin_advanced.ps1"
echo Attempt-Login >> "%TEMP%\iblogin_advanced.ps1"
echo Write-Host "Press any key to try again or Ctrl+C to exit" >> "%TEMP%\iblogin_advanced.ps1"
echo $null = $host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown") >> "%TEMP%\iblogin_advanced.ps1"
echo Attempt-Login >> "%TEMP%\iblogin_advanced.ps1"

REM Run the PowerShell script in a visible window to allow for retry
echo Starting login script with retry capability (PowerShell window will open)...
start powershell -NoExit -ExecutionPolicy Bypass -File "%TEMP%\iblogin_advanced.ps1"

echo IB Gateway login process started with retry capability.
echo - The PowerShell window will remain open to allow for manual retry if needed.
echo - Press any key in the PowerShell window to attempt login again.
echo - Close the PowerShell window when done.
