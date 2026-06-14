from django.db.models import Count
from api.models import AcademicLoad  # Замените your_app на название вашего приложения

def remove_academic_load_duplicates():
    # 1. Находим критерии дубликатов
    # Группируем по нужным полям и считаем количество вхождений
    AcademicLoad.objects.exclude(study_group__study_program__institute__short_name="ИВИТШ").prefetch_related("study_group__study_program__institute").delete()
# Запуск функции
remove_academic_load_duplicates()