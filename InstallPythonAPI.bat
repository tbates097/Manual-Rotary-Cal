@echo off
::Check permissions
net session >nul 2>&1
if not %errorLevel% == 0 (
	echo This batch file must be ran as administrator
	echo Right click on the batch file and select "Run as administrator"
	pause
	exit
)

@echo off
SetLocal

set Automation1Dir=

rem Test if the key can be found before trying to parse in the installation directory
REG QUERY "HKEY_LOCAL_MACHINE\SOFTWARE\Aerotech\Automation1" /v "InstallDir" >nul 2>nul

if not ERRORLEVEL 1 (
	rem echo CVS Registry Key was found, parsing location...
	FOR /F "tokens=2* skip=2" %%a in ('REG QUERY "HKEY_LOCAL_MACHINE\SOFTWARE\Aerotech\Automation1" /v "InstallDir"') do set Automation1Dir=%%b
) 
if "%Automation1Dir%" == "" (
	rem echo CVS Registry Key was not found, checking default location...
	if exist "C:\Program Files\Aerotech\Automation1-MDK\APIs\Python\automation1\" (
		set Automation1Dir=C:\Program Files\Aerotech\Automation1-MDK\
	) else (
		echo Cannot find Automation1 Python API in any known installation location. Please install manually!
		pause
		exit /b 1
	)
)
if exist "%Automation1Dir%APIs\Python\automation1\" (
	rem echo Found Python API installation directory!
	set APIFilepath="%Automation1Dir%APIs\Python\automation1"
) else (
	echo Automation1 Python API not found in installation directory! 
	echo It should be here: "%Automation1Dir%APIs\Python\automation1\"
	echo The installed version of Automation1 may not have the API...
	pause
	exit /b 1
)
echo.
echo Automation1 Python API is about to be installed from the following location:
echo %APIFilepath%
echo.
echo Press CTRL+C to cancel . . .
pause
echo.
echo Select environment to install API
CALL conda env list
set /p "environment=Enter environment: "
CALL conda deactivate
CALL conda activate %environment%
rem uninstall old version
CALL pip uninstall automation1 -y
CALL pip install %APIFilepath%
CALL conda deactivate
echo Finished!
echo.
pause

