@echo off
REM Send-Pakket Platform - Database Backup Script
REM This script creates backups of the PostgreSQL database

echo ========================================
echo Send-Pakket Database Backup Script
echo ========================================

REM Configuration
set BACKUP_DIR=backups
set TIMESTAMP=%date:~-4,4%%date:~-10,2%%date:~-7,2%_%time:~0,2%%time:~3,2%%time:~6,2%
set BACKUP_FILE=%BACKUP_DIR%\sendpakket_backup_%TIMESTAMP%.sql

REM Create backup directory if it doesn't exist
if not exist %BACKUP_DIR% mkdir %BACKUP_DIR%

echo Creating database backup...
echo Backup file: %BACKUP_FILE%

REM Run backup using docker-compose
docker-compose exec -T db pg_dump -U sendpakket_user -d sendpakket > %BACKUP_FILE%

if errorlevel 1 (
    echo ERROR: Database backup failed!
    exit /b 1
)

echo SUCCESS: Database backup created at %BACKUP_FILE%

REM Compress the backup (optional)
echo Compressing backup file...
powershell "Compress-Archive -Path '%BACKUP_FILE%' -DestinationPath '%BACKUP_FILE%.zip' -Force"
if exist "%BACKUP_FILE%.zip" (
    del %BACKUP_FILE%
    echo Backup compressed to: %BACKUP_FILE%.zip
)

REM Clean up old backups (keep last 30 days)
echo Cleaning up old backups (keeping last 30 days)...
forfiles /p %BACKUP_DIR% /m *.zip /d -30 /c "cmd /c del @path"

echo.
echo ========================================
echo Backup completed successfully!
echo ========================================