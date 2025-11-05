@echo off
chcp 65001 > nul

ECHO === Checking Docker Installation First ===
REM First check if Docker is installed and running
call check_and_install_docker.bat
IF %errorlevel% NEQ 0 (
    ECHO Please install Docker Desktop before continuing.
    PAUSE
    EXIT /b 1
)

ECHO === Building Docker Image ===

REM Build Docker image
docker build -t ai-travel-planner .

IF %errorlevel% NEQ 0 (
    ECHO Docker image build failed!
    PAUSE
    EXIT /b 1
)

ECHO Build successful! Image name: ai-travel-planner
ECHO.
ECHO === Optional Operations ===
ECHO 1. Run Docker container with audio support: docker run -d -p 5000:5000 --device /dev/snd:/dev/snd ai-travel-planner
ECHO 2. Export image file: docker save -o ai-travel-planner.tar ai-travel-planner
ECHO 3. View image: docker images ai-travel-planner

ECHO.
ECHO Press any key to exit...
PAUSE > nul