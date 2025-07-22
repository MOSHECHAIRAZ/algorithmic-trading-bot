@echo off
echo Starting IB Gateway with IBController directly...

REM Set paths without Hebrew characters
set IBGW_PATH=C:\Jts\ibgateway\1037\ibgateway.exe
set IBC_PATH=C:\IBController
set IBC_INI=C:\IBController\IBController.ini

REM Launch IB Gateway with IBController's Java component
java -cp "%IBC_PATH%\IBController.jar" ibcontroller.IBController "%IBGW_PATH%" "%IBC_INI%"

echo IBController started.
