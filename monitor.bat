@echo off
REM Send-Pakket Platform - Production Monitoring Script
REM This script provides monitoring and maintenance commands

echo ========================================
echo Send-Pakket Platform Monitoring
echo ========================================

if "%1"=="status" goto status
if "%1"=="logs" goto logs
if "%1"=="restart" goto restart
if "%1"=="backup" goto backup
if "%1"=="health" goto health
if "%1"=="cleanup" goto cleanup

echo Usage: monitor.bat [command]
echo.
echo Commands:
echo   status   - Show status of all services
echo   logs     - Show logs from all services
echo   restart  - Restart all services
echo   backup   - Create database backup
echo   health   - Run health checks
echo   cleanup  - Clean up Docker resources
goto end

:status
echo Checking service status...
docker-compose ps
goto end

:logs
echo Showing recent logs...
docker-compose logs --tail=100 -f
goto end

:restart
echo Restarting services...
docker-compose restart
echo Services restarted.
goto end

:backup
echo Creating database backup...
call backup.bat
goto end

:health
echo Running health checks...
echo Web Application Health:
curl -s http://localhost/health/ || echo "Web health check failed"
echo.
echo Database Health:
docker-compose exec db pg_isready -U sendpakket_user -d sendpakket || echo "Database health check failed"
echo.
echo Redis Health:
docker-compose exec redis redis-cli ping || echo "Redis health check failed"
goto end

:cleanup
echo Cleaning up Docker resources...
docker system prune -f
docker volume prune -f
echo Cleanup completed.
goto end

:end
echo.
echo ========================================