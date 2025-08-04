@echo off
echo =================================
echo Watch Scraping Tool Setup
echo =================================

REM Check if Python is installed
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo Error: Python is not installed or not in PATH
    echo Please install Python 3.8+ and try again
    pause
    exit /b 1
)

echo Python is installed

REM Install dependencies
echo Installing dependencies...
pip install -r requirements.txt

if %errorlevel% neq 0 (
    echo Error installing dependencies
    pause
    exit /b 1
)

echo Dependencies installed successfully

REM Run setup test
echo Running setup test...
python test_setup.py

echo.
echo Setup completed!
echo.
echo Available commands:
echo   python main.py                          - Run all scrapers
echo   python main.py --sites chronofinder     - Run specific scraper
echo   python main.py --list-sites             - List available scrapers
echo   python scrapers/chronofinder_scraper.py - Run individual scraper
echo.

pause
