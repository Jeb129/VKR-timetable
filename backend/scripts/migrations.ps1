cd ..\
venv\Scripts\Activate
python manage.py makemigrations api
python manage.py makemigrations authentification
python manage.py migrate
pause