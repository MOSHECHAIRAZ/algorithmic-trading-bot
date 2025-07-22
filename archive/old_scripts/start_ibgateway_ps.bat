@echo off
echo Starting IB Gateway with IBController via PowerShell...

powershell -Command "& {
  $env:TWS_MAJOR_VRSN = '1037'
  $env:IBC_INI = 'C:\IBController\IBController.ini'
  $env:IBC_PATH = 'C:\IBController'
  $env:TWS_PATH = 'C:\Jts'
  $env:LOG_PATH = 'C:\IBController\Logs'
  
  Set-Location 'C:\IBController'
  
  # Run IBControllerGatewayStart.bat but with direct invocation to avoid path issues
  & java -cp 'C:\IBController\IBController.jar' ibcontroller.IBController 'C:\Jts\ibgateway\1037\ibgateway.exe' 'C:\IBController\IBController.ini'
}"

echo IBController launched via PowerShell.
