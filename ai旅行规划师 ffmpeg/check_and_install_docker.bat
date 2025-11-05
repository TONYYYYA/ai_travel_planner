@echo off
chcp 65001 > nul

ECHO === Checking Docker Installation ===

REM Check if Docker is installed
where docker > nul 2> nul
IF %errorlevel% NEQ 0 (
    ECHO Docker is not installed on your system.
    ECHO.
    ECHO === Docker Installation Guide ===
    ECHO 1. Download Docker Desktop for Windows from: https://www.docker.com/products/docker-desktop/
    ECHO 2. Run the installer and follow the installation wizard
    ECHO 3. Restart your computer when prompted
    ECHO 4. After restart, Docker Desktop should start automatically
    ECHO 5. Open Docker Desktop and wait until it shows "Docker Desktop is running"
    ECHO 6. Open a new command prompt and run 'docker --version' to verify
    ECHO.
    ECHO Once Docker is installed and running, you can run build_docker.bat again.
    PAUSE
    EXIT /b 1
) ELSE (
    ECHO Docker is installed!
    docker --version
    ECHO.
    ECHO Checking if Docker Desktop is running...
    
    REM Try to run a simple Docker command to check if it's running
    docker info > nul 2> nul
    IF %errorlevel% NEQ 0 (
        ECHO Docker command is available but Docker Desktop may not be running.
        ECHO Please start Docker Desktop and try again.
        PAUSE
        EXIT /b 1
    ) ELSE (
        ECHO Docker Desktop is running. You can now build your Docker image.
        PAUSE
        EXIT /b 0
    )
)