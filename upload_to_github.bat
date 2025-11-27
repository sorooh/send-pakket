@echo off
REM Send-Pakket Platform - GitHub Upload Script
REM This script helps upload the project to GitHub

echo ========================================
echo Send-Pakket Platform - GitHub Upload
echo ========================================

REM Check if git is initialized
if not exist .git (
    echo Initializing Git repository...
    git init
    git add .
    git commit -m "Initial commit: Send-Pakket Platform v1.0"
) else (
    echo Git repository already exists.
)

echo.
echo Next steps to upload to GitHub:
echo.
echo 1. Create a new repository on GitHub:
echo    - Go to https://github.com/new
echo    - Repository name: sendpakket-platform
echo    - Make it public or private
echo    - DON'T initialize with README
echo.
echo 2. Copy the repository URL and run:
echo    git remote add origin https://github.com/YOUR_USERNAME/sendpakket-platform.git
echo    git branch -M main
echo    git push -u origin main
echo.
echo 3. Enable GitHub Actions in your repository settings
echo.
echo 4. For one-click deployment:
echo    - Go to repository Settings ^> Pages
echo    - Enable GitHub Pages from main branch
echo.
echo 5. Choose your deployment platform:
echo    - Railway: Connect repo and deploy automatically
echo    - Render: Use render.yaml for auto-deployment
echo    - Fly.io: Use fly.toml for deployment
echo    - Heroku: Connect repo for auto-deployment
echo.
echo ========================================
echo Your app will be ready for deployment! 🚀
echo ========================================