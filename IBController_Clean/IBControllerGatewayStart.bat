@echo off
setlocal enableextensions enabledelayedexpansion


::=============================================================================+
::                                                                             +
::   This command file starts the IB Gateway, which provides a low-resource    + 
::   capability for running TWS API programs without the complex TWS user      +
::   interface.                                                                +
::                                                                             +
::   If you run it without any arguments it will display a new window showing  +
::   useful information and then start the Gateway. If you supply /INLINE as   +
::   the first argument, the information will be displayed in the current      +
::   command prompt window. (If you are using Task Scheduler to run this, you  +
::   MUST supply the /INLINE argument to ensure correct operation.)            +
::                                                                             +
::   The following lines, beginning with 'set', are the only ones you may      +
::   need to change, and you probably only need to change the first one.       +
::                                                                             +
::   The notes below give further information on why you might need to         +
::   change them.                                                              +
::                                                                             +
::=============================================================================+


set TWS_MAJOR_VRSN=1037
set IBC_INI=C:\Users\משה\פרויקט קופילוט למידת מכונה\IBController_Clean\IBController.ini
set TRADING_MODE=
set IBC_PATH=C:\Users\משה\פרויקט קופילוט למידת מכונה\IBController_Clean
set TWS_PATH=C:\Jts
set LOG_PATH=%IBC_PATH%\Logs
set TWSUSERID=
set TWSPASSWORD=
set FIXUSERID=
set FIXPASSWORD=
set JAVA_PATH=
set HIDE=


::  PLEASE DON'T CHANGE ANYTHING BELOW THIS LINE !!
::==============================================================================

::   Notes:
::

::   TWS_MAJOR_VRSN
::
::     Specifies the major version number of Gateway to be run. If you are 
::     unsure of which version number to use, run the Gateway manually from the 
::     icon on the desktop, then click Help > About IB Gateway. In the 
::     displayed information you'll see a line similar to this:
::
::       Build 954.2a, Oct 30, 2015 4:07:54 PM
::
::     Here the major version number is 954. Do not include the rest of the 
::     version number in this setting.


::   IBC_INI
::
::     This is the location and filename of the IBController configuration file.
::     This file should be in a folder in your personal filestore, so that
::     other users of your computer can't access it. This folder and its 
::     contents should also be encrypted so that even users with administrator 
::     privileges can't see the contents. Note that you can use the HOMEDRIVE and
::     HOMEPATH environment variables to address the root of your personal 
::     filestore they are set automatically by Windows).


::   TRADING_MODE
::
::     TWS 955 introduced a new Trading Mode combo box on its login dialog. 
::     This indicates whether the live account or the paper trading account 
::     corresponding to the supplied credentials is to be used. The values 
::     allowed here are 'live' and 'paper' (not case-sensitive). For earlier 
::     versions of TWS, setting this has no effect. If no value is specified 
::     here, the value is taken from the TradingMode setting in the 
::     configuration file. If no value is specified there either, the value 
::     'live' is assumed.


::   IBC_PATH
::
::     The folder containing the IBController files. 


::   TWS_PATH
::
::     The folder where TWS is installed. The TWS installer always installs to 
::     C:\Jts. Note that even if you have installed from a Gateway download
::     rather than a TWS download, you should still use this default setting.
::     It is possibe to move the TWS installation to a different folder, but
::     there are virtually no good reasons for doing so.


::   LOG_PATH
::
::     Specifies the folder where diagnostic information is to be logged while 
::     this command file is running. This information is very valuable when 
::     troubleshooting problems, so it is advisable to always have this set to
::     a valid location, especially when setting up IBController. You must
::     have write access to the specified folder.
::
::     Once everything runs properly, you can prevent further logging by 
::     removing the value as show below (but this is not recommended): 
::
::     set LOG_PATH=


::   TWSUSERID
::   TWSPASSWORD
::
::     If your TWS user id and password are not included in your IBController 
::     configuration file, you can set them here (do not encrypt the password). 
::     However you are strongly advised not to set them here because this file 
::     is not normally in a protected location.


::   FIXUSERID
::   FIXPASSWORD
::
::     If you are running the FIX Gateway (for which you must set FIX=yes in 
::     your IBController configuration file), and the FIX user id and password 
::     are not included in the configuration file, you can set them here (do 
::     not encrypt the password). However you are strongly advised not to set 
::     them here because this file is not normally in a protected location.


::   JAVA_PATH
::
::     IB's installer for TWS/Gateway includes a hidden version of Java which 
::     IB have used to develop and test that particular version. This means that
::     it is not necessary to separately install Java. If there is a separate
::     Java installation, that does not matter: it won't be used by IBController 
::     or TWS/Gateway unless you set the path to it here. You should not do this 
::     without a very good reason.


::   HIDE
::
::     If set to YES or TRUE, the diagnostic window that contains information 
::     about the running TWS, and where to find the log file, will be minimized 
::     to the taskbar. If not set, or set to any other value, the window will be 
::     displayed. Values are not case-sensitive so for example yEs and yes will 
::     be interpeted as YES. (Note that when the /INLINE argument is supplied,
::     this setting has no effect.)


::   End of Notes:
::==============================================================================

set APP=GATEWAY
set TITLE=IBController (%APP% %TWS_MAJOR_VRSN%)
if /I "%HIDE%" == "YES" (
    set MIN=/Min
) else if /I "%HIDE%" == "TRUE" (
    set MIN=/Min
) else (
    set MIN=
)

if /I "%~1" == "/INLINE" (
	echo Calling DisplayBannerAndLaunch...
	call "%IBC_PATH%\Scripts\DisplayBannerAndLaunch.bat"
) else (
	start "%TITLE%" %MIN% "%IBC_PATH%\Scripts\DisplayBannerAndLaunch.bat"
)
