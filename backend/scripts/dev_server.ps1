cd ..\
venv\Scripts\Activate
$env:DJANGO_SETTINGS_MODULE="config.settings.dev"
python manage.py migrate
python manage.py runserver
