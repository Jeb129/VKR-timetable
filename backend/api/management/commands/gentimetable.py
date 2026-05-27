from django.core.management.base import BaseCommand, CommandError
from api.models import Semester, ScheduleScenario
from api.services.schedule.generator import TimetableGenerator
from django.utils import timezone

class Command(BaseCommand):
    help = 'Генерирует расписание для указанного семестра в новом сценарии'

    def add_arguments(self, parser):
        parser.add_argument('semester_id', type=int, help='ID семестра')
        parser.add_argument('--iter', type=int, default=10000, help='Количество итераций')
        parser.add_argument('--name', type=str, help='Название сценария')

    def handle(self, *args, **options):
        semester_id = options['semester_id']
        iterations = options['iter']
        
        try:
            semester = Semester.objects.get(id=semester_id)
        except Semester.DoesNotExist:
            raise CommandError(f'Семестр с ID {semester_id} не найден')

        # 1. Создаем новый сценарий
        name = options['name'] or f"Авто-сценарий {timezone.now().strftime('%Y-%m-%d %H:%M')}"
        scenario = ScheduleScenario.objects.create(
            name=name,
            semester=semester,
            is_active=False
        )
        
        self.stdout.write(self.style.SUCCESS(f"Создан сценарий: {scenario.name} (ID: {scenario.id})"))

        # 2. Запускаем генератор
        generator = TimetableGenerator(scenario.id)
        
        self.stdout.write("Начало генерации...")
        try:
            lessons, final_penalty = generator.run(iterations=iterations)
            
            # 3. Сохраняем
            self.stdout.write("Сохранение в базу данных...")
            generator.commit(lessons)
            
            self.stdout.write(self.style.SUCCESS(
                f"Успешно! Сгенерировано занятий: {len(lessons)}. Итоговый штраф: {final_penalty}"
            ))
            
        except Exception as e:
            scenario.delete() # Удаляем пустой сценарий при ошибке
            raise CommandError(f"Ошибка при генерации: {str(e)}")