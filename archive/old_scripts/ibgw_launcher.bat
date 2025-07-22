@echo off
echo Starting IB Gateway with IBController...

REM Path to IBGateway executable
set GW_PATH=C:\Jts\ibgateway\1037\ibgateway.exe

REM Path to Java
set JAVA_PATH=java

REM Path to IBController JAR
set IBC_JAR=C:\IBController\IBController.jar

REM Path to INI file
set IBC_INI=C:\IBController\IBController.ini

REM Launch IBController with IBGateway
echo Launching IBController...
"%JAVA_PATH%" -cp "%IBC_JAR%" ibcontroller.IBController "%GW_PATH%" "%IBC_INI%"

echo IBController process started.
