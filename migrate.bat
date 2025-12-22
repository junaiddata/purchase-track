@echo off
call venv\Scripts\activate
python manage.py makemigrations tracking > migration_output.txt 2>&1
python manage.py migrate >> migration_output.txt 2>&1
echo Migration complete >> migration_output.txt
