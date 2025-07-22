@echo off
setlocal enableextensions enabledelayedexpansion

echo Starting IBController Gateway...

:: Set the main variables like the original script
set TWS_VERSION=1037
set ENTRY_POINT=ibcontroller.IBGatewayController
set TWS_MAIN_PATH=C:\Jts\ibgateway\%TWS_VERSION%
set TWSCP=
set INSTALL4J=%TWS_MAIN_PATH%\.install4j

:: First, build the classpath like IBController does
echo Building classpath...

:: Get IBController jar
for %%f in ("%~dp0IBController.jar") do set TWSCP=!TWSCP!;%%f

:: Add all jars from the TWS installation
for %%f in ("%TWS_MAIN_PATH%\*.jar") do set TWSCP=!TWSCP!;%%f

echo Classpath built: %TWSCP%

:: Find Java like IBController does
echo Looking for Java installation...
set JAVA_PATH=

if exist "%INSTALL4J%\pref_jre.cfg" (
    echo Reading pref_jre.cfg...
    for /f "tokens=1 delims=" %%i in (%INSTALL4J%\pref_jre.cfg) do (
        set JAVA_PATH=%%i\bin
        echo Found Java path: !JAVA_PATH!
        if exist "!JAVA_PATH!\java.exe" (
            echo Java executable found
            goto :java_found
        ) else (
            echo Java executable not found at !JAVA_PATH!
            set JAVA_PATH=
        )
    )
)

:java_found
if not defined JAVA_PATH (
    echo Checking inst_jre.cfg...
    if exist "%INSTALL4J%\inst_jre.cfg" (
        for /f "tokens=1 delims=" %%i in (%INSTALL4J%\inst_jre.cfg) do (
            set JAVA_PATH=%%i\bin
            echo Found Java path: !JAVA_PATH!
            if exist "!JAVA_PATH!\java.exe" (
                echo Java executable found
                goto :java_found2
            ) else (
                echo Java executable not found at !JAVA_PATH!
                set JAVA_PATH=
            )
        )
    )
)

:java_found2
if not defined JAVA_PATH (
    echo Checking system Java...
    if exist "%PROGRAMDATA%\Oracle\Java\javapath\java.exe" (
        set JAVA_PATH=%PROGRAMDATA%\Oracle\Java\javapath
        echo Using system Java: !JAVA_PATH!
    )
)

if not defined JAVA_PATH (
    echo Error: Can't find suitable Java installation
    pause
    exit /b 1
)

echo Using Java at: %JAVA_PATH%

:: Read VM options like IBController does
echo Reading VM options...
set VMOPTS=
if exist "%TWS_MAIN_PATH%\ibgateway.vmoptions" (
    for /f "tokens=1 delims=" %%i in (%TWS_MAIN_PATH%\ibgateway.vmoptions) do (
        set VMOPTS=!VMOPTS! %%i
    )
)

echo VM Options: %VMOPTS%

:: Start the Gateway like IBController does
echo Starting Gateway with IBController...

"%JAVA_PATH%\java.exe" %VMOPTS% ^
    -cp "%TWSCP%" ^
    %ENTRY_POINT% ^
    "%~dp0IBController.ini"

echo Gateway process ended with code: %ERRORLEVEL%
pause
