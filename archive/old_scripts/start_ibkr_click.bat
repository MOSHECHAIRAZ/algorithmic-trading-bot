@echo off
:: IBKR Gateway Click-Based Approach
:: This script uses mouse clicks to ensure we target the right fields

echo IBKR Gateway Click-Based Login Approach
echo ---------------------------------------------------

REM Start Gateway
echo Starting IBKR Gateway...
start "" "C:\Jts\ibgateway\1037\ibgateway.exe"

REM Wait for Gateway to initialize
echo Waiting for Gateway to fully initialize (15 seconds)...
timeout /t 15 /nobreak > nul

REM Create PowerShell script for mouse control
echo Creating mouse control script...
echo $username = "bvqcpy485" > mouse_control.ps1
echo $password = "R0533124116" >> mouse_control.ps1
echo Add-Type -AssemblyName System.Windows.Forms >> mouse_control.ps1
echo Add-Type -AssemblyName System.Drawing >> mouse_control.ps1

REM Function to click and type
echo function Click-And-Type { >> mouse_control.ps1
echo     param($x, $y, $text) >> mouse_control.ps1
echo     [System.Windows.Forms.Cursor]::Position = New-Object System.Drawing.Point($x, $y) >> mouse_control.ps1
echo     Start-Sleep -Milliseconds 200 >> mouse_control.ps1
echo     [System.Windows.Forms.SendKeys]::SendWait('{CLICK}') >> mouse_control.ps1
echo     Start-Sleep -Milliseconds 500 >> mouse_control.ps1
echo     [System.Windows.Forms.SendKeys]::SendWait('^a') >> mouse_control.ps1
echo     Start-Sleep -Milliseconds 200 >> mouse_control.ps1
echo     [System.Windows.Forms.SendKeys]::SendWait('{DELETE}') >> mouse_control.ps1
echo     Start-Sleep -Milliseconds 200 >> mouse_control.ps1
echo     foreach($char in $text.ToCharArray()) { >> mouse_control.ps1
echo         [System.Windows.Forms.SendKeys]::SendWait($char) >> mouse_control.ps1
echo         Start-Sleep -Milliseconds 50 >> mouse_control.ps1
echo     } >> mouse_control.ps1
echo     Write-Host "Typed: $text" >> mouse_control.ps1
echo } >> mouse_control.ps1

REM Show all windows
echo Write-Host "Showing Desktop and then restoring windows..." >> mouse_control.ps1
echo (New-Object -ComObject Shell.Application).MinimizeAll() >> mouse_control.ps1
echo Start-Sleep -Seconds 1 >> mouse_control.ps1
echo (New-Object -ComObject Shell.Application).UndoMinimizeAll() >> mouse_control.ps1
echo Start-Sleep -Seconds 2 >> mouse_control.ps1

REM Try multiple positions for username field
echo Write-Host "Trying multiple positions for username field..." >> mouse_control.ps1

REM Try multiple positions for username - many possible screen positions
echo $possibleUsernamePositions = @( >> mouse_control.ps1
echo     @{x=300; y=250}, >> mouse_control.ps1
echo     @{x=400; y=250}, >> mouse_control.ps1
echo     @{x=300; y=300}, >> mouse_control.ps1
echo     @{x=400; y=300}, >> mouse_control.ps1
echo     @{x=500; y=300}, >> mouse_control.ps1
echo     @{x=300; y=350}, >> mouse_control.ps1
echo     @{x=400; y=350}, >> mouse_control.ps1
echo     @{x=500; y=350} >> mouse_control.ps1
echo ) >> mouse_control.ps1

echo foreach($pos in $possibleUsernamePositions) { >> mouse_control.ps1
echo     Write-Host "Trying username at position: $($pos.x), $($pos.y)" >> mouse_control.ps1
echo     Click-And-Type -x $pos.x -y $pos.y -text $username >> mouse_control.ps1
echo     Start-Sleep -Milliseconds 500 >> mouse_control.ps1
echo } >> mouse_control.ps1

REM Try multiple positions for password field (typically below username)
echo Write-Host "Trying multiple positions for password field..." >> mouse_control.ps1

echo $possiblePasswordPositions = @( >> mouse_control.ps1
echo     @{x=300; y=300}, >> mouse_control.ps1
echo     @{x=400; y=300}, >> mouse_control.ps1
echo     @{x=300; y=350}, >> mouse_control.ps1
echo     @{x=400; y=350}, >> mouse_control.ps1
echo     @{x=500; y=350}, >> mouse_control.ps1
echo     @{x=300; y=400}, >> mouse_control.ps1
echo     @{x=400; y=400}, >> mouse_control.ps1
echo     @{x=500; y=400} >> mouse_control.ps1
echo ) >> mouse_control.ps1

echo foreach($pos in $possiblePasswordPositions) { >> mouse_control.ps1
echo     Write-Host "Trying password at position: $($pos.x), $($pos.y)" >> mouse_control.ps1
echo     Click-And-Type -x $pos.x -y $pos.y -text $password >> mouse_control.ps1
echo     Start-Sleep -Milliseconds 500 >> mouse_control.ps1
echo } >> mouse_control.ps1

REM Press Enter
echo Write-Host "Pressing Enter to login..." >> mouse_control.ps1
echo [System.Windows.Forms.SendKeys]::SendWait('{ENTER}') >> mouse_control.ps1

REM Run the PowerShell script
echo Running mouse control script...
powershell -ExecutionPolicy Bypass -File mouse_control.ps1

echo Login attempt complete.
echo Cleaning up...
timeout /t 3 /nobreak > nul
del mouse_control.ps1
