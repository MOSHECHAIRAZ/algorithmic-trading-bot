@echo off
setlocal enableextensions enabledelayedexpansion

:: Simple IBController Gateway Start
set TWS_MAJOR_VRSN=1037
set IBC_INI=IBController.ini
set IBC_PATH=%cd%
set TWS_PATH=C:\Jts
set JAVA_PATH=

echo Starting IB Gateway with IBController...
echo Using credentials from IBController.ini

:: Launch IBController directly
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
     ibcontroller.IBGatewayController ^
     IBController.ini

echo Gateway finished.
pause
