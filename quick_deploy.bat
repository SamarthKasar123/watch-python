@echo off
REM 🚀 Quick Deploy Script - Watch Scraping System (Windows)
REM This script prepares your project for deployment to Render

echo 🔧 Preparing Watch Scraping System for Deployment...
echo ==================================================

REM Check if git is initialized
if not exist ".git" (
    echo 📁 Initializing Git repository...
    git init
    echo ✅ Git initialized
) else (
    echo ✅ Git repository already exists
)

REM Stage all files
echo 📦 Adding files to Git...
git add .

REM Commit changes
echo 💾 Committing changes...
git commit -m "Production ready - Watch Scraping System with Dashboard - Features: Professional dashboard with 178 real products, 2 working scrapers, REST APIs, deployment ready"

echo.
echo 🎉 SUCCESS! Your project is ready for deployment!
echo ==================================================
echo.
echo 📋 NEXT STEPS:
echo 1. Go to: https://render.com
echo 2. Sign up/Login with GitHub
echo 3. Click 'New' → 'Web Service'
echo 4. Connect this Git repository
echo 5. Use these settings:
echo    - Build Command: pip install -r requirements.txt
echo    - Start Command: python dashboard/app.py
echo    - Environment: Python 3
echo.
echo ⏱️  Deployment time: ~10-15 minutes
echo 💰 Cost: FREE (with Render free tier)
echo 🔗 You'll get: https://your-project-name.onrender.com
echo.
echo 📖 For detailed instructions, see: DEPLOYMENT_GUIDE.md
echo 🎯 For client delivery info, see: FINAL_CLIENT_PACKAGE.md
echo.
echo 🚀 Ready to go live!
pause
