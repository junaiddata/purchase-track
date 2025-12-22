@echo off
echo Starting setup... > output.log
python -m venv venv
call venv\Scripts\activate
pip install django pandas openpyxl >> output.log
django-admin startproject purchase_tracking .
python manage.py startapp tracking
python manage.py migrate
echo Setup complete >> output.log
