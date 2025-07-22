@echo off
echo Starting IB Gateway directly...

REM Path to IBGateway executable
set GW_PATH=C:\Jts\ibgateway\1037\ibgateway.exe

REM Launch IB Gateway - note: parameters might differ between versions
echo Launching IB Gateway...
start "" "%GW_PATH%"

REM Wait for the gateway to start
timeout /t 5 /nobreak > nul

REM Run AutoIt script to handle login
echo Sending login credentials...
powershell -Command @"
Add-Type -AssemblyName System.Windows.Forms
Start-Sleep -Seconds 5
[System.Windows.Forms.SendKeys]::SendWait('ליאור21')
[System.Windows.Forms.SendKeys]::SendWait('{TAB}')
[System.Windows.Forms.SendKeys]::SendWait('Abcd1234')
[System.Windows.Forms.SendKeys]::SendWait('{ENTER}')
"@

echo IB Gateway should be logging in now.
