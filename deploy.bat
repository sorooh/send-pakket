@echo off
REM Send-Pakket Platform - Production Deployment Script
REM This script handles the complete production deployment process

echo ========================================
echo Send-Pakket Platform Deployment Script
echo ========================================

REM Check if Docker is installed
docker --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Docker is not installed. Please install Docker first.
    exit /b 1
)

REM Check if docker-compose is available
docker-compose --version >nul 2>&1
if errorlevel 1 (
    docker compose version >nul 2>&1
    if errorlevel 1 (
        echo ERROR: Docker Compose is not available. Please install Docker Compose.
        exit /b 1
    )
    set COMPOSE_CMD=docker compose
) else (
    set COMPOSE_CMD=docker-compose
)

REM Check if .env.prod exists
if not exist .env.prod (
    echo ERROR: .env.prod file not found. Please copy .env.example to .env.prod and configure your production settings.
    exit /b 1
)

echo Step 1: Pulling latest changes...
git pull origin main

echo Step 2: Building Docker images...
%COMPOSE_CMD% build --no-cache

echo Step 3: Starting database and Redis...
%COMPOSE_CMD% up -d db redis

echo Waiting for database to be ready...
timeout /t 30 /nobreak >nul

echo Step 4: Running database migrations...
%COMPOSE_CMD% run --rm web python manage.py migrate

echo Step 5: Collecting static files...
%COMPOSE_CMD% run --rm web python manage.py collectstatic --noinput --clear

echo Step 6: Creating superuser (if needed)...
%COMPOSE_CMD% run --rm web python manage.py createsuperuser --noinput || echo "Superuser may already exist"

echo Step 7: Starting all services...
%COMPOSE_CMD% up -d

echo Step 8: Running health check...
timeout /t 10 /nobreak >nul
curl -f http://localhost/health/ >nul 2>&1
if errorlevel 1 (
    echo WARNING: Health check failed. Services may still be starting up.
) else (
    echo SUCCESS: Health check passed!
)

echo.
echo ========================================
echo Deployment completed successfully!
echo.
echo Services running:
echo - Web Application: http://localhost
echo - Admin Interface: http://localhost/admin/
echo - API Documentation: http://localhost/api/docs/
echo - Health Check: http://localhost/health/
echo.
echo To view logs: %COMPOSE_CMD% logs -f
echo To stop services: %COMPOSE_CMD% down
echo ========================================