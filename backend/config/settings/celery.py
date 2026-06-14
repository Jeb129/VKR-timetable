import os
from celery import Celery

# Указываем переменную окружения с настройками Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.prod')

app = Celery('timetable_project')

# Загружаем настройки из settings.py с префиксом CELERY_
# Например: CELERY_BROKER_URL = 'redis://localhost:6379/0'
app.config_from_object('django.conf:settings', namespace='CELERY')

# Автоматически ищем задачи в файлах tasks.py внутри приложений
app.autodiscover_tasks()

@app.task(bind=True)
def debug_task(self):
    print(f'Request: {self.request!r}')