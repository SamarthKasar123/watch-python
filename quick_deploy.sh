#!/bin/bash

# 🚀 Quick Deploy Script - Watch Scraping System
# This script prepares your project for deployment to Render

echo "🔧 Preparing Watch Scraping System for Deployment..."
echo "=================================================="

# Check if git is initialized
if [ ! -d ".git" ]; then
    echo "📁 Initializing Git repository..."
    git init
    echo "✅ Git initialized"
else
    echo "✅ Git repository already exists"
fi

# Create .gitignore if it doesn't exist
if [ ! -f ".gitignore" ]; then
    echo "📝 Creating .gitignore..."
    cat > .gitignore << EOF
__pycache__/
*.pyc
*.pyo
*.pyd
.Python
env/
venv/
.venv/
pip-log.txt
pip-delete-this-directory.txt
.tox/
.coverage
.coverage.*
.cache
nosetests.xml
coverage.xml
*.cover
*.log
.git/
.mypy_cache/
.pytest_cache/
.hypothesis/
node_modules/
.DS_Store
*.swp
*.swo
*~
.idea/
.vscode/
*.sqlite
*.db
.env
EOF
    echo "✅ .gitignore created"
fi

# Stage all files
echo "📦 Adding files to Git..."
git add .

# Commit changes
echo "💾 Committing changes..."
git commit -m "Production ready - Watch Scraping System with Dashboard

Features:
- Professional dashboard with 178 real products
- 2 working scrapers (ChronoFinder, BQ Watches)
- REST APIs and export functionality
- Deployment ready configuration
- Modern responsive UI with real-time charts"

echo ""
echo "🎉 SUCCESS! Your project is ready for deployment!"
echo "=================================================="
echo ""
echo "📋 NEXT STEPS:"
echo "1. Go to: https://render.com"
echo "2. Sign up/Login with GitHub"
echo "3. Click 'New' → 'Web Service'"
echo "4. Connect this Git repository"
echo "5. Use these settings:"
echo "   - Build Command: pip install -r requirements.txt"
echo "   - Start Command: python dashboard/app.py"
echo "   - Environment: Python 3"
echo ""
echo "⏱️  Deployment time: ~10-15 minutes"
echo "💰 Cost: FREE (with Render free tier)"
echo "🔗 You'll get: https://your-project-name.onrender.com"
echo ""
echo "📖 For detailed instructions, see: DEPLOYMENT_GUIDE.md"
echo "🎯 For client delivery info, see: FINAL_CLIENT_PACKAGE.md"
echo ""
echo "🚀 Ready to go live!"
