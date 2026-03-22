@echo off
setlocal

cd /d "%~dp0"

:: Create virtualenv if it doesn't exist
if not exist "venv\" (
    echo [*] Creating virtual environment...
    virtualenv venv
    if errorlevel 1 (
        echo [!] Failed to create virtual environment.
        echo     Make sure virtualenv is installed: pip install virtualenv
        pause
        exit /b 1
    )
)

:: Activate virtual environment
call venv\Scripts\activate.bat

:: Install/update dependencies
echo [*] Installing dependencies...
pip install -q -r requirements.txt

:: Check for .env file
if not exist ".env" (
    if exist ".env.example" (
        copy ".env.example" ".env" >nul
        echo.
        echo [!] .env file created from .env.example
        echo     Edit .env with your Spotify credentials before running again.
        echo.
        pause
        exit /b 1
    ) else (
        echo [!] No .env file found. Create one with SPOTIPY_CLIENT_ID, SPOTIPY_CLIENT_SECRET, etc.
        pause
        exit /b 1
    )
)

:: Validate required env vars
for /f "tokens=1,2 delims==" %%a in (.env) do (
    if "%%a"=="SPOTIPY_CLIENT_ID" set CLIENT_ID=%%b
    if "%%a"=="SPOTIPY_CLIENT_SECRET" set CLIENT_SECRET=%%b
)

if "%CLIENT_ID%"=="" (
    echo [!] SPOTIPY_CLIENT_ID not set in .env
    pause
    exit /b 1
)
if "%CLIENT_ID%"=="your_client_id_here" (
    echo [!] SPOTIPY_CLIENT_ID not set in .env
    pause
    exit /b 1
)
if "%CLIENT_SECRET%"=="" (
    echo [!] SPOTIPY_CLIENT_SECRET not set in .env
    pause
    exit /b 1
)
if "%CLIENT_SECRET%"=="your_client_secret_here" (
    echo [!] SPOTIPY_CLIENT_SECRET not set in .env
    pause
    exit /b 1
)

if not exist "flask_session\" mkdir flask_session

echo [*] Starting Spotify Manager at http://127.0.0.1:5000
python run.py

pause
