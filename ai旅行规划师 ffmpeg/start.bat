@echo on
chcp 65001 > nul
setlocal

REM AI Travel Planner Startup Script
ECHO ==================================
ECHO AI Travel Planner - Window Will Stay Open
ECHO ==================================
ECHO Current Script Path: %~dp0
set VENV_NAME=venv

REM 1. Check Python Installation
ECHO Checking Python installation...
python --version > nul 2>&1
if %errorlevel% neq 0 (
    ECHO ERROR: Python not found. Please install Python 3.8+
    ECHO Press any key to continue...
    pause > nul
    goto KEEP_OPEN
)
ECHO Python check completed!

REM 2. Check and Create Virtual Environment
ECHO.
ECHO Checking virtual environment...
if not exist "%VENV_NAME%" (
    ECHO Creating virtual environment...
    python -m venv %VENV_NAME%
    if %errorlevel% neq 0 (
        ECHO ERROR: Failed to create virtual environment.
        ECHO Try running as administrator.
        ECHO Press any key to continue...
        pause > nul
        goto KEEP_OPEN
    )
    ECHO Virtual environment created successfully!
) else (
    ECHO Virtual environment already exists.
)

REM 3. Activate Virtual Environment
ECHO Activating virtual environment...
call "%VENV_NAME%\Scripts\activate.bat"
if %errorlevel% neq 0 (
    ECHO ERROR: Failed to activate virtual environment.
    ECHO Possible reasons: insufficient permissions or corrupted files.
    ECHO Press any key to continue...
    pause > nul
    goto KEEP_OPEN
)
ECHO Virtual environment activated successfully!

REM 4. Upgrade pip
ECHO Upgrading pip...
pip install --upgrade pip > nul 2>&1 || ECHO WARNING: pip upgrade failed, continuing...

REM 5. Check and Enter backend Directory
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

REM 6. Install Dependencies
ECHO Installing project dependencies...
pip install -r requirements.txt
if %errorlevel% neq 0 (
    ECHO ERROR: Failed to install dependencies.
    ECHO Check network connection or requirements.txt
    ECHO Press any key to continue...
    pause > nul
    goto KEEP_OPEN
)
ECHO Dependencies installed successfully!

REM 7. Check app.py File
if not exist "app.py" (
    ECHO ERROR: app.py file not found.
    ECHO Current directory contents:
    dir /b
    ECHO Press any key to continue...
    pause > nul
    goto KEEP_OPEN
)

REM 8. Start Application
ECHO.
ECHO ==================================
ECHO Starting Flask application...
ECHO ==================================
ECHO Application starting. Window will remain open.
ECHO Opening browser at http://127.0.0.1:5000 in 3 seconds...

REM Open default browser with delay to allow server to start
start /b cmd /c "timeout /t 3 > nul && start http://127.0.0.1:5000"

REM Run the application
python app.py || ECHO WARNING: Application may have stopped running

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