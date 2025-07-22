@echo off
setlocal enableextensions enabledelayedexpansion

:: Fixed version of IBController Gateway Start for paths with non-ASCII characters
set TWS_MAJOR_VRSN=1037
set IBC_INI=%~dp0IBController.ini
set TRADING_MODE=
set IBC_PATH=%~dp0
set TWS_PATH=C:\Jts
set LOG_PATH=%IBC_PATH%Logs
set JAVA_PATH=

:: Create logs directory if it doesn't exist
if not exist "%LOG_PATH%" mkdir "%LOG_PATH%"

:: Set log file with simpler name
set LOG_FILE=%LOG_PATH%\gateway.log

echo Starting IB Gateway with IBController...

:: Launch IBController using the actual working method
cd /d "%IBC_PATH%"

java -cp "IBController.jar;C:\Jts\ibgateway\1037\jars\*" ^
     -Xmx512M ^
     -XX:+UseG1GC ^
     --add-opens java.desktop/javax.swing=ALL-UNNAMED ^
     --add-opens java.desktop/java.awt=ALL-UNNAMED ^
     --add-opens java.base/java.lang=ALL-UNNAMED ^
     -Dsun.java2d.noddraw=true ^
     -Dswing.boldMetal=false ^
     -Dsun.locale.formatasdefault=true ^
     -Djava.awt.headless=false ^
     -DIBController.LogToConsole=yes ^
     ibcontroller.IBGatewayController ^
     "IBController.ini"

if errorlevel 1 (
    echo Error occurred. Check log: %LOG_FILE%
) else (
    echo Gateway started successfully.
)

if errorlevel 1 (
    echo +
    echo +                       **** An error has occurred ****
    echo +
    echo +                     Please look in the diagnostics file 
    echo +                   %LOG_FILE%
    echo +                     for further information
    echo +
    echo + Press any key to close this window
    pause > NUL
) else (
    echo + GATEWAY %TWS_MAJOR_VRSN% has finished
)

echo +
echo +==============================================================================
echo.
