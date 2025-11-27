@echo off
echo 🚀 Send-Pakket Platform - GitHub Upload Script
echo ===============================================
echo.
echo This script will help you upload your Send-Pakket platform to GitHub
echo and enable one-click deployment to multiple cloud platforms.
echo.
echo Prerequisites:
echo 1. Create a new GitHub repository (public or private)
echo 2. Copy the repository URL (e.g., https://github.com/yourusername/send-pakket-platform.git)
echo.
set /p REPO_URL="Enter your GitHub repository URL: "
echo.
echo Adding remote origin...
git remote add origin %REPO_URL%
echo.
echo Pushing to GitHub...
git push -u origin master
echo.
echo ✅ SUCCESS! Your Send-Pakket platform is now on GitHub!
echo.
echo 🎯 Next Steps:
echo 1. Go to your GitHub repository
echo 2. Click the deployment buttons in README.md to deploy instantly
echo 3. Set up secrets in repository settings for automated deployments
echo.
echo 🔗 Deployment Platforms Ready:
echo - Railway: Click the Railway button in README.md
echo - Render: Click the Render button in README.md
echo - Fly.io: Click the Fly.io button in README.md
echo - Heroku: Click the Heroku button in README.md
echo.
echo 📋 Required Secrets for GitHub Actions:
echo - RAILWAY_TOKEN: Your Railway API token
echo - RENDER_API_KEY: Your Render API key
echo - FLY_API_TOKEN: Your Fly.io API token
echo - HEROKU_API_KEY: Your Heroku API key
echo.
echo 🎉 Your platform is ready to compete globally!
pause