#!/bin/bash

echo "================================="
echo "Watch Scraping Tool Setup"
echo "================================="

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "Error: Python 3 is not installed"
    echo "Please install Python 3.8+ and try again"
    exit 1
fi

echo "Python is installed"

# Install dependencies
echo "Installing dependencies..."
pip3 install -r requirements.txt

if [ $? -ne 0 ]; then
    echo "Error installing dependencies"
    exit 1
fi

echo "Dependencies installed successfully"

# Run setup test
echo "Running setup test..."
python3 test_setup.py

echo ""
echo "Setup completed!"
echo ""
echo "Available commands:"
echo "  python3 main.py                          - Run all scrapers"
echo "  python3 main.py --sites chronofinder     - Run specific scraper"
echo "  python3 main.py --list-sites             - List available scrapers"
echo "  python3 scrapers/chronofinder_scraper.py - Run individual scraper"
echo ""
