@echo off
setlocal enabledelayedexpansion

echo Starting IB Gateway with Slow Typing Auto-Login (using PowerShell to read credentials)...

REM Create a temporary PowerShell script to read the JSON file
echo Creating script to read credentials from config file...
echo $configPath = 'c:\Users\משה\פרויקט קופילוט למידת מכונה\system_config.json' > "%TEMP%\read_config.ps1"
echo $config = Get-Content -Raw -Path $configPath ^| ConvertFrom-Json >> "%TEMP%\read_config.ps1"
echo "USERNAME=" + $config.ibkr_settings.username >> "%TEMP%\read_config.ps1"
echo "PASSWORD=" + $config.ibkr_settings.password >> "%TEMP%\read_config.ps1"
echo "GATEWAY_PATH=" + $config.ibkr_settings.gateway_path >> "%TEMP%\read_config.ps1"

REM Execute the PowerShell script and capture the output
echo Reading credentials from config file...
for /f "tokens=1,* delims==" %%a in ('powershell -ExecutionPolicy Bypass -File "%TEMP%\read_config.ps1"') do (
  if "%%a"=="USERNAME" (
    set IBKR_USERNAME=%%b
  )
  if "%%a"=="PASSWORD" (
    set IBKR_PASSWORD=%%b
  )
  if "%%a"=="GATEWAY_PATH" (
    set GW_PATH=%%b
  )
)

REM Delete the temporary PowerShell script
del "%TEMP%\read_config.ps1"

echo Found credentials: %IBKR_USERNAME% / [PROTECTED]
echo Gateway Path: %GW_PATH%

REM Launch IB Gateway
echo Launching IB Gateway...
start "" %GW_PATH%

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
