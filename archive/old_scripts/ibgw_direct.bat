@echo off
echo Starting IB Gateway directly...

REM Path to IBGateway executable
set GW_PATH=C:\Jts\ibgateway\1037\ibgateway.exe

REM Launch IB Gateway
echo Launching IB Gateway...
start "" "%GW_PATH%" "-user" "lior21" "-pw" "Abcd1234" "-mode" "live"

echo IB Gateway process started.
