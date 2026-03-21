from config.settings.base import *
# Костыль, т.к. пока нет БД. Можно закоментить и бек будет пытаться работать с Postgre
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / '../db.sqlite3',
    }
}

DEBUG = True
CORS_ALLOW_ALL_ORIGINS = True

