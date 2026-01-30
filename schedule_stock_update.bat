@echo off
REM This batch file runs the stock import command
REM Schedule this to run every 5 minutes using Windows Task Scheduler

cd /d "%~dp0"
call venv\Scripts\activate.bat
python manage.py import_stock_api
deactivate
