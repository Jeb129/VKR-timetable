venv\Scripts\Activate
$env:DJANGO_SETTINGS_MODULE="config.settings.prod"
python manage.py collectstatic
python win_prod.py
Write-Output "Сервер запущен"