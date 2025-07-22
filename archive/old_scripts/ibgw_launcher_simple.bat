@echo off
echo Starting IB Gateway with IBController...

REM Path to IBGateway executable
set GW_PATH=C:\Jts\ibgateway\1037\ibgateway.exe

REM Path to Java
set JAVA_PATH=java

REM Path to IBController JAR
set IBC_JAR=C:\IBController\IBController.jar

REM Launch IBController directly (without specifying INI path - it will find the default one)
echo Launching IBController...
"%JAVA_PATH%" -cp "%IBC_JAR%" ibcontroller.IBController "%GW_PATH%"

echo IBController process started.
