@echo on
chcp 65001 > nul
setlocal

REM AI Travel Planner Startup Script
ECHO ==================================
ECHO AI Travel Planner - Window Will Stay Open
ECHO ==================================
ECHO Current Script Path: %~dp0

REM Set Anaconda environment path (using relative path)
set "ANACONDA_ENV_PATH=%~dp0aitravel2"

REM 1. Check Anaconda Environment
ECHO Checking Anaconda environment...
if not exist "%ANACONDA_ENV_PATH%" (
    ECHO ERROR: Anaconda environment not found at %ANACONDA_ENV_PATH%
    ECHO Please ensure the environment exists and the path is correct.
    ECHO Press any key to continue...
    pause > nul
    goto KEEP_OPEN
)
ECHO Anaconda environment found at %ANACONDA_ENV_PATH%

REM 2. Set Python command path from Anaconda environment
SET "ANACONDA_PYTHON=%ANACONDA_ENV_PATH%\python.exe"
ECHO Using Python from Anaconda environment: %ANACONDA_PYTHON%

REM 3. Check if Python executable exists
if not exist "%ANACONDA_PYTHON%" (
    ECHO ERROR: Python executable not found at %ANACONDA_PYTHON%
    ECHO Press any key to continue...
    pause > nul
    goto KEEP_OPEN
)
ECHO Python check completed!

REM 4. Create virtual environment in venv folder
set "VENV_NAME=venv"
set "VENV_PATH=%~dp0%VENV_NAME%"

ECHO. 
ECHO ==================================
ECHO Creating virtual environment using Anaconda Python...
ECHO Virtual environment will be created at: %VENV_PATH%
ECHO ==================================

REM Check if virtual environment already exists
if exist "%VENV_PATH%" (
    ECHO Virtual environment already exists. Skipping creation.
) else (
    ECHO Creating new virtual environment...
    "%ANACONDA_PYTHON%" -m venv "%VENV_PATH%"
    if %errorlevel% neq 0 (
        ECHO ERROR: Failed to create virtual environment.
        ECHO Press any key to continue...
        pause > nul
        goto KEEP_OPEN
    )
    ECHO Virtual environment created successfully!
)

REM 5. Set Python and pip commands from virtual environment
SET "PYTHON_CMD=%VENV_PATH%\Scripts\python.exe"
SET "PIP_CMD=%VENV_PATH%\Scripts\pip.exe"
ECHO Using Python from virtual environment: %PYTHON_CMD%
ECHO Using pip from virtual environment: %PIP_CMD%

REM 6. Check if pip executable exists
if not exist "%PIP_CMD%" (
    ECHO ERROR: pip executable not found at %PIP_CMD%
    ECHO Press any key to continue...
    pause > nul
    goto KEEP_OPEN
)

REM 7. Upgrade pip
ECHO Upgrading pip...
"%PIP_CMD%" install --upgrade pip > nul 2>&1 || ECHO WARNING: pip upgrade failed, continuing...

REM 8. Check and Enter backend Directory
ECHO.
ECHO Checking backend directory...
if not exist "backend" (
    ECHO ERROR: backend directory not found.
    ECHO Current directory contents:
    dir /b
    ECHO Press any key to continue...
    pause > nul
    goto KEEP_OPEN
)

cd backend
ECHO Current working directory: %cd%

REM 9. Install Dependencies
ECHO Installing project dependencies...
"%PIP_CMD%" install -r requirements.txt
if %errorlevel% neq 0 (
    ECHO ERROR: Failed to install dependencies.
    ECHO Check network connection or requirements.txt
    ECHO Press any key to continue...
    pause > nul
    goto KEEP_OPEN
)
ECHO Dependencies installed successfully!

REM 10. Check app.py File
if not exist "app.py" (
    ECHO ERROR: app.py file not found.
    ECHO Current directory contents:
    dir /b
    ECHO Press any key to continue...
    pause > nul
    goto KEEP_OPEN
)

REM 11. Start Application
ECHO.
ECHO ==================================
ECHO Starting Flask application from virtual environment...
ECHO ==================================
ECHO Application starting. Window will remain open.
ECHO Opening browser at http://127.0.0.1:5000 in 3 seconds...

REM Open default browser with delay to allow server to start
start /b cmd /c "timeout /t 3 > nul && start http://127.0.0.1:5000"

REM Run the application using virtual environment Python
"%PYTHON_CMD%" app.py || ECHO WARNING: Application may have stopped running

:KEEP_OPEN
ECHO.
ECHO ==================================
ECHO Script execution completed or error occurred.
ECHO Window will remain open for you to view messages.
ECHO To close this window, click the X button in the top-right corner.
ECHO ==================================

:LOOP
ECHO Window kept open. Press Ctrl+C and then Y to exit (or click X to close).
pause > nul
goto LOOP

endlocal