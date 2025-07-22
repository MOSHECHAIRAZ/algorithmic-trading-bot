@echo off
setlocal enabledelayedexpansion

echo Interactive IB Gateway Auto-Login

REM Get credentials from the user
set /p IBKR_USERNAME=Enter your IB Gateway username: 
set /p IBKR_PASSWORD=Enter your IB Gateway password: 

REM Path to IBGateway executable
set GW_PATH=C:\Jts\ibgateway\1037\ibgateway.exe

echo Using credentials: %IBKR_USERNAME% / [PROTECTED]
echo Gateway Path: %GW_PATH%

REM Launch IB Gateway
echo Launching IB Gateway...
start "" "%GW_PATH%"

REM Create PowerShell script for slow and careful typing
echo Creating slow typing login script...
echo $username = '%IBKR_USERNAME%' > "%TEMP%\iblogin_slow.ps1"
echo $password = '%IBKR_PASSWORD%' >> "%TEMP%\iblogin_slow.ps1"
echo Add-Type -AssemblyName System.Windows.Forms >> "%TEMP%\iblogin_slow.ps1"
echo function Type-SlowAndCareful($text) { >> "%TEMP%\iblogin_slow.ps1"
echo   foreach ($char in $text.ToCharArray()) { >> "%TEMP%\iblogin_slow.ps1"
echo     [System.Windows.Forms.SendKeys]::SendWait($char) >> "%TEMP%\iblogin_slow.ps1"
echo     Start-Sleep -Milliseconds 300 >> "%TEMP%\iblogin_slow.ps1"
echo     Write-Host -NoNewline "." >> "%TEMP%\iblogin_slow.ps1"
echo   } >> "%TEMP%\iblogin_slow.ps1"
echo   Write-Host "" >> "%TEMP%\iblogin_slow.ps1"
echo } >> "%TEMP%\iblogin_slow.ps1"

echo Write-Host "Waiting 25 seconds for IB Gateway to fully load..." >> "%TEMP%\iblogin_slow.ps1"
echo Start-Sleep -Seconds 25 >> "%TEMP%\iblogin_slow.ps1"
echo Write-Host "Typing username slowly: " -NoNewline >> "%TEMP%\iblogin_slow.ps1"
echo Type-SlowAndCareful $username >> "%TEMP%\iblogin_slow.ps1"
echo Write-Host "Pressing TAB key..." >> "%TEMP%\iblogin_slow.ps1"
echo [System.Windows.Forms.SendKeys]::SendWait('{TAB}') >> "%TEMP%\iblogin_slow.ps1"
echo Start-Sleep -Seconds 1 >> "%TEMP%\iblogin_slow.ps1"
echo Write-Host "Typing password slowly: " -NoNewline >> "%TEMP%\iblogin_slow.ps1"
echo Type-SlowAndCareful $password >> "%TEMP%\iblogin_slow.ps1"
echo Write-Host "Pressing ENTER key..." >> "%TEMP%\iblogin_slow.ps1"
echo [System.Windows.Forms.SendKeys]::SendWait('{ENTER}') >> "%TEMP%\iblogin_slow.ps1"
echo Write-Host "Login attempt completed!" >> "%TEMP%\iblogin_slow.ps1"
echo Write-Host "Press any key to try again or Ctrl+C to exit..." >> "%TEMP%\iblogin_slow.ps1"
echo $null = $host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown") >> "%TEMP%\iblogin_slow.ps1"

echo Write-Host "`n`nTrying again with longer wait time..." >> "%TEMP%\iblogin_slow.ps1"
echo Start-Sleep -Seconds 5 >> "%TEMP%\iblogin_slow.ps1"
echo [System.Windows.Forms.SendKeys]::SendWait('^a') >> "%TEMP%\iblogin_slow.ps1"
echo Start-Sleep -Milliseconds 500 >> "%TEMP%\iblogin_slow.ps1"
echo [System.Windows.Forms.SendKeys]::SendWait('{DEL}') >> "%TEMP%\iblogin_slow.ps1"
echo Start-Sleep -Milliseconds 500 >> "%TEMP%\iblogin_slow.ps1"
echo Write-Host "Typing username slowly (second attempt): " -NoNewline >> "%TEMP%\iblogin_slow.ps1"
echo Type-SlowAndCareful $username >> "%TEMP%\iblogin_slow.ps1"
echo [System.Windows.Forms.SendKeys]::SendWait('{TAB}') >> "%TEMP%\iblogin_slow.ps1"
echo Start-Sleep -Seconds 1 >> "%TEMP%\iblogin_slow.ps1"
echo Write-Host "Typing password slowly (second attempt): " -NoNewline >> "%TEMP%\iblogin_slow.ps1"
echo Type-SlowAndCareful $password >> "%TEMP%\iblogin_slow.ps1"
echo [System.Windows.Forms.SendKeys]::SendWait('{ENTER}') >> "%TEMP%\iblogin_slow.ps1"
echo Write-Host "Second login attempt completed!" >> "%TEMP%\iblogin_slow.ps1"
echo Write-Host "Press any key to exit..." >> "%TEMP%\iblogin_slow.ps1"
echo $null = $host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown") >> "%TEMP%\iblogin_slow.ps1"

REM Run the PowerShell script in a visible window
echo Starting slow typing login script in a PowerShell window...
start powershell -NoExit -ExecutionPolicy Bypass -File "%TEMP%\iblogin_slow.ps1"

echo IB Gateway login process started with slow typing.
echo - The PowerShell window will remain open to allow for manual retry if needed.
echo - Press any key in the PowerShell window to attempt login again.
echo - Close the PowerShell window when done.
