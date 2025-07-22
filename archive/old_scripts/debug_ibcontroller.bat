@echo off
echo Working directory:
cd
echo.
echo Checking file existence:
if exist "c:\Users\משה\פרויקט קופילוט למידת מכונה\IBController\IBControllerGatewayStart.bat" (
    echo IBControllerGatewayStart.bat exists
) else (
    echo IBControllerGatewayStart.bat does not exist
)

echo Attempting to run script...
cd /d "c:\Users\משה\פרויקט קופילוט למידת מכונה\IBController"
call "IBControllerGatewayStart.bat"
pause
