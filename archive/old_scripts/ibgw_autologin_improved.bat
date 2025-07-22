@echo off
echo Starting IB Gateway directly...

REM Path to IBGateway executable
set GW_PATH=C:\Jts\ibgateway\1037\ibgateway.exe

REM Launch IB Gateway
echo Launching IB Gateway...
start "" "%GW_PATH%"

REM Create PowerShell script for auto-login
echo Creating temporary login script...
echo Add-Type -AssemblyName System.Windows.Forms > "%TEMP%\iblogin.ps1"
echo Start-Sleep -Seconds 15 >> "%TEMP%\iblogin.ps1"
echo Write-Host "Attempting to send login credentials..." >> "%TEMP%\iblogin.ps1"
echo [System.Windows.Forms.SendKeys]::SendWait('ליאור21') >> "%TEMP%\iblogin.ps1"
echo Start-Sleep -Seconds 1 >> "%TEMP%\iblogin.ps1"
echo [System.Windows.Forms.SendKeys]::SendWait('{TAB}') >> "%TEMP%\iblogin.ps1"
echo Start-Sleep -Seconds 1 >> "%TEMP%\iblogin.ps1"
echo [System.Windows.Forms.SendKeys]::SendWait('Abcd1234') >> "%TEMP%\iblogin.ps1"
echo Start-Sleep -Seconds 1 >> "%TEMP%\iblogin.ps1"
echo [System.Windows.Forms.SendKeys]::SendWait('{ENTER}') >> "%TEMP%\iblogin.ps1"
echo Write-Host "Login credentials sent!" >> "%TEMP%\iblogin.ps1"

REM Run the PowerShell script
echo Waiting for IB Gateway to load (15 seconds)...
echo This window will stay open while the login process completes.
start powershell -ExecutionPolicy Bypass -File "%TEMP%\iblogin.ps1"

echo IB Gateway login process started. Please wait...
timeout /t 20 /nobreak > nul
del "%TEMP%\iblogin.ps1"
echo Login attempt completed.
