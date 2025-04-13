@echo off
REM Migration Runner Script for Windows

setlocal enabledelayedexpansion

REM Default values
set MODE=migrate
set BATCH_SIZE=
set MAX_CONCURRENT=
set CONFIG_FILE=config.yaml

REM Parse command line arguments
:parse_args
if "%~1"=="" goto :run_migration
if "%~1"=="--mode" (
    set MODE=%~2
    shift
    shift
    goto :parse_args
)
if "%~1"=="--batch-size" (
    set BATCH_SIZE=%~2
    shift
    shift
    goto :parse_args
)
if "%~1"=="--max-concurrent" (
    set MAX_CONCURRENT=%~2
    shift
    shift
    goto :parse_args
)
if "%~1"=="--config" (
    set CONFIG_FILE=%~2
    shift
    shift
    goto :parse_args
)
if "%~1"=="--help" (
    echo Usage: %0 [OPTIONS]
    echo Options:
    echo   --mode MODE              Migration mode (migrate^|webhook^|both)
    echo   --batch-size SIZE        Override batch size
    echo   --max-concurrent NUM     Override max concurrent downloads
    echo   --config FILE            Configuration file path
    echo   --help                   Show this help message
    exit /b 0
)
echo Unknown option: %~1
exit /b 1

:run_migration
REM Check if virtual environment exists
if not exist venv (
    echo ❌ Virtual environment not found. Run setup.bat first.
    pause
    exit /b 1
)

REM Activate virtual environment
call venv\Scripts\activate.bat

REM Check if .env file exists
if not exist .env (
    echo ❌ .env file not found. Run setup.bat first.
    pause
    exit /b 1
)

REM Check if Google credentials exist
if not exist credentials\google-service-account.json (
    echo ❌ Google service account credentials not found.
    echo Please place your google-service-account.json file in the credentials\ directory.
    pause
    exit /b 1
)

REM Build command
set CMD=python main.py --mode %MODE% --config %CONFIG_FILE%

if not "%BATCH_SIZE%"=="" (
    set CMD=%CMD% --batch-size %BATCH_SIZE%
)

if not "%MAX_CONCURRENT%"=="" (
    set CMD=%CMD% --max-concurrent %MAX_CONCURRENT%
)

echo 🚀 Starting migration with mode: %MODE%
echo Command: %CMD%
echo.

REM Run the migration
%CMD%

# tweak 12 at 2025-09-26 19:30:06
