@echo off
echo Starting IB Gateway with Slow Typing Auto-Login (reading credentials from system_config.json)...

REM Get credentials from system_config.json
echo Reading login credentials from system_config.json...
for /f "tokens=2 delims=:," %%a in ('findstr "username" "c:\Users\משה\פרויקט קופילוט למידת מכונה\system_config.json"') do (
    set IBKR_USERNAME=%%a
    set IBKR_USERNAME=!IBKR_USERNAME:"=!
    set IBKR_USERNAME=!IBKR_USERNAME: =!
)

for /f "tokens=2 delims=:," %%a in ('findstr "password" "c:\Users\משה\פרויקט קופילוט למידת מכונה\system_config.json"') do (
    set IBKR_PASSWORD=%%a
    set IBKR_PASSWORD=!IBKR_PASSWORD:"=!
    set IBKR_PASSWORD=!IBKR_PASSWORD: =!
)

REM Get gateway path from system_config.json
for /f "tokens=2 delims=:," %%a in ('findstr "gateway_path" "c:\Users\משה\פרויקט קופילוט למידת מכונה\system_config.json"') do (
    set GW_PATH=%%a
    set GW_PATH=!GW_PATH:"=!
    set GW_PATH=!GW_PATH:\\=\!
    set GW_PATH=!GW_PATH: =!
)

echo Found credentials: %IBKR_USERNAME% / [PROTECTED]
echo Gateway Path: %GW_PATH%

REM Launch IB Gateway
echo Launching IB Gateway...
start "" "%GW_PATH%"

REM Create PowerShell script for slow and careful typing
echo Creating slow typing login script with credentials from system_config.json...
echo ^REM הפרטים שנלקחו מקובץ ההגדרות system_config.json
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
