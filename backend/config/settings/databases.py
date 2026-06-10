import os

# Database
# https://docs.djangoproject.com/en/6.0/ref/settings/#databases

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": os.getenv("POSTGRES_DB"),
        "USER": os.getenv("POSTGRES_USER"),
        "PASSWORD": os.getenv("POSTGRES_PASSWORD"),
        "HOST": os.getenv("POSTGRES_HOST"),
        "PORT": os.getenv("POSTGRES_PORT"),
    }
}

REDIS = {
    "HOST": os.getenv("REDIS_HOST", "localhost"),
    "PORT": int(os.getenv("REDIS_PORT", "6379")),
    "DB": os.getenv("REDIS_DB", "1"),
    "PASSWORD": os.getenv("REDIS_PASSWORD", "123321"),
}
