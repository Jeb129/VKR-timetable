from django.core.management.base import BaseCommand
from api.models.schedule import Semester, ScheduleScenario
from datetime import date

class Command(BaseCommand):
    help = 'Инициализация семестра и активация сценария EIOS'

    def handle(self, *args, **options):
        # 1. Создаем или получаем семестр
        # Мы берем период, покрывающий март 2026 года
        sem_name = "Весенний семестр 2026"
        semester, created = Semester.objects.get_or_create(
            name=sem_name,
            defaults={
                "date_start": date(2026, 2, 1),
                "date_end": date(2026, 7, 31)
            }
        )

        if created:
            self.stdout.write(self.style.SUCCESS(f"Создан новый семестр: {sem_name}"))
        else:
            self.stdout.write(f"Семестр '{sem_name}' уже существует.")

        # 2. Ищем сценарий импорта и привязываем его
        scenario = ScheduleScenario.objects.filter(name="EIOS Import").first()

        if scenario:
            # Сначала деактивируем все остальные сценарии в этом семестре, 
            # чтобы не нарушить UniqueConstraint (одно активное на семестр)
            ScheduleScenario.objects.filter(semester=semester, is_active=True).update(is_active=False)
            
            # Обновляем наш целевой сценарий
            scenario.semester = semester
            scenario.is_active = True
            scenario.save()
            
            self.stdout.write(self.style.SUCCESS(
                f"Сценарий '{scenario.name}' привязан к семестру и АКТИВИРОВАН."
            ))
        else:
            self.stdout.write(self.style.ERROR(
                "ОШИБКА: Сценарий 'EIOS Import' не найден. "
                "Сначала запустите команду sync_eios."
            ))

        self.stdout.write(self.style.MIGRATE_LABEL("--- Настройка завершена ---"))