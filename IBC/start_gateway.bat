::
:: IBC Launcher for IBKR Gateway
::

@echo off
echo Starting IBKR Gateway using IBC...

:: Set paths
set TWS_PATH=C:\Jts\ibgateway\1037
set TWS_FILENAME=ibgateway.exe
set IBC_PATH=%~dp0

:: Configuration
set CONFIG_FILE=%IBC_PATH%config.ini
set LOG_FILE=%IBC_PATH%ibc.log
set TRADING_MODE=live
set USERID=bvqcpy485
set PASSWORD=R0533124116

:: Create VBS file for automatic login
echo Creating auto-login script...
echo Set WshShell = WScript.CreateObject("WScript.Shell") > %IBC_PATH%login.vbs
echo WScript.Sleep 3000 >> %IBC_PATH%login.vbs
echo WshShell.AppActivate "IB Gateway" >> %IBC_PATH%login.vbs
echo WScript.Sleep 1000 >> %IBC_PATH%login.vbs
echo WshShell.SendKeys "%USERID%" >> %IBC_PATH%login.vbs
echo WshShell.SendKeys "{TAB}" >> %IBC_PATH%login.vbs
echo WScript.Sleep 200 >> %IBC_PATH%login.vbs
echo WshShell.SendKeys "%PASSWORD%" >> %IBC_PATH%login.vbs
echo WScript.Sleep 200 >> %IBC_PATH%login.vbs
echo WshShell.SendKeys "{ENTER}" >> %IBC_PATH%login.vbs

:: Start Gateway
echo Starting IBKR Gateway...
start "" "%TWS_PATH%\%TWS_FILENAME%"

:: Wait a bit and then run the login script
echo Waiting for gateway to start...
timeout /t 3 /nobreak > nul
echo Running auto-login...
start /min wscript.exe "%IBC_PATH%login.vbs"

echo Process started. Please wait for the login screen to appear.
