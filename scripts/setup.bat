@echo off
REM Slack Archive Migration Tool Setup Script for Windows

echo 🚀 Setting up Slack Archive Migration Tool...

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python is required but not installed.
    echo Please install Python 3.11+ from https://python.org
    pause
    exit /b 1
)

echo ✅ Python is installed

REM Create virtual environment
echo 📦 Creating virtual environment...
python -m venv venv
call venv\Scripts\activate.bat

REM Install dependencies
echo 📥 Installing dependencies...
python -m pip install --upgrade pip
pip install -r requirements.txt

REM Create necessary directories
echo 📁 Creating directories...
if not exist logs mkdir logs
if not exist data mkdir data
if not exist downloads mkdir downloads
if not exist credentials mkdir credentials
if not exist ssl mkdir ssl

REM Copy configuration files
echo ⚙️ Setting up configuration...
if not exist .env (
    copy env.example .env
    echo 📝 Created .env file. Please update it with your credentials.
) else (
    echo 📝 .env file already exists.
)

if not exist config.yaml (
    echo 📝 Configuration file already exists.
)

REM Set up Google Apps Script
echo 🔧 Setting up Google Apps Script...
if not exist google_apps_script mkdir google_apps_script

echo ✅ Setup complete!
echo.
echo Next steps:
echo 1. Update .env with your Slack and Google Cloud credentials
echo 2. Place your Google service account JSON file in credentials/
echo 3. Update config.yaml with your preferences
echo 4. Run: python main.py --mode migrate
echo.
echo For Docker setup, run: docker-compose up -d
pause
