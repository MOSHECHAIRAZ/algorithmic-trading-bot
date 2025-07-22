@echo off
setlocal enableextensions enabledelayedexp# Find Java like IBController does
set JAVA_PATH=
if exist "%INSTALL4J%\pref_jre.cfg" (
    for /f "tokens=1 delims=" %%i in (%INSTALL4J%\pref_jre.cfg) do (
        set JAVA_PATH=%%i\bin
        goto :java_found
    )
)

:java_found
if not exist "%JAVA_PATH%\java.exe" set JAVA_PATH=

if not defined JAVA_PATH (
    if exist "%INSTALL4J%\inst_jre.cfg" (
        for /f "tokens=1 delims=" %%i in (%INSTALL4J%\inst_jre.cfg) do (
            set JAVA_PATH=%%i\bin
            if exist "!JAVA_PATH!\java.exe" goto :java_found2
        )
    )
)

:java_found2
if not defined JAVA_PATH (
    if exist "%PROGRAMDATA%\Oracle\Java\javapath\java.exe" set JAVA_PATH=%PROGRAMDATA%\Oracle\Java\javapath
)arting IBController Gateway...

:: Set the main variables like the original script
set TWS_VERSION=1037
set ENTRY_POINT=ibcontroller.IBGatewayController
set TWS_PATH=C:\Jts
set IBC_PATH=%~dp0
set IBC_INI=%IBC_PATH%IBController.ini

:: Check if files exist
if not exist "%TWS_PATH%\ibgateway\%TWS_VERSION%\jars" (
    echo Error: TWS Gateway jars directory not found
    pause
    exit /b 1
)

if not exist "%IBC_INI%" (
    echo Error: IBController.ini not found
    pause
    exit /b 1
)

:: Use the .vmoptions file from Gateway
set TWS_VMOPTS=%TWS_PATH%\ibgateway\%TWS_VERSION%\ibgateway.vmoptions
set TWS_JARS=%TWS_PATH%\ibgateway\%TWS_VERSION%\jars
set INSTALL4J=%TWS_PATH%\ibgateway\%TWS_VERSION%\.install4j

echo Generating the classpath...

:: Build classpath like IBController does
set IBC_CLASSPATH=
for %%i in (%TWS_JARS%\*.jar) do (
    if not "!IBC_CLASSPATH!"=="" set IBC_CLASSPATH=!IBC_CLASSPATH!;
    set IBC_CLASSPATH=!IBC_CLASSPATH!%%i
)
set IBC_CLASSPATH=%IBC_CLASSPATH%;%IBC_PATH%IBController.jar

echo Generating the JAVA VM options...

:: Read VM options from .vmoptions file like IBController does
set JAVA_VM_OPTIONS=
for /f "tokens=1 delims= " %%i in (%TWS_VMOPTS%) do (
    set TOKEN=%%i
    if not "!TOKEN!"=="" (
        if not "!TOKEN:~0,1!"=="#" set JAVA_VM_OPTIONS=!JAVA_VM_OPTIONS! %%i
    )
)

echo Determining Java location...

:: Find Java like IBController does
set JAVA_PATH=
if exist "%INSTALL4J%\pref_jre.cfg" (
    for /f "tokens=1 delims=" %%i in (%INSTALL4J%\pref_jre.cfg) do set JAVA_PATH=%%i\bin
    if not exist "!JAVA_PATH!\java.exe" set JAVA_PATH=
)

if not defined JAVA_PATH (
    if exist "%INSTALL4J%\inst_jre.cfg" (
        for /f "tokens=1 delims=" %%i in (%INSTALL4J%\inst_jre.cfg) do set JAVA_PATH=%%i\bin
        if not exist "!JAVA_PATH!\java.exe" set JAVA_PATH=
    )
)

if not defined JAVA_PATH (
    if exist "%PROGRAMDATA%\Oracle\Java\javapath\java.exe" set JAVA_PATH="%PROGRAMDATA%\Oracle\Java\javapath"
)

if not defined JAVA_PATH (
    echo Error: Can't find suitable Java installation
    pause
    exit /b 1
)

echo Java path: %JAVA_PATH%
echo Starting IBController...

:: Change to TWS directory like IBController does
pushd %TWS_PATH%

:: Run with the exact same parameters as IBController
"%JAVA_PATH%\java.exe" -cp "%IBC_CLASSPATH%" %JAVA_VM_OPTIONS% %ENTRY_POINT% "%IBC_INI%"

popd

echo IBController finished
pause
