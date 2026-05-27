from django.core.management.base import BaseCommand, CommandError
from api.models import AcademicLoad,Semester
from api.services.schedule.planner import generate_planned_lessons_bulk

class Command(BaseCommand):
    help = "Генерация агрегированных плановых занятий на основе академической нагрузки"

    def add_arguments(self, parser):
        parser.add_argument("semester_id", type=int, help="ID семестра")

    def handle(self, *args, **options):
        semester_id = options["semester_id"]
        
        try:
            semester = Semester.objects.get(pk=semester_id)
        except Semester.DoesNotExist:
            raise CommandError(f"Семестр {semester_id} не найден")

        # Предварительная загрузка связей для ускорения make_final_key
        self.stdout.write(f"Начинаю обработку семестра {semester}")

        loads = AcademicLoad.objects.filter(semester=semester).select_related(
            "discipline", "lesson_type", "study_group"
        )

        if not loads.exists():
            self.stdout.write("Нет нагрузки для обработки.")
            return

        self.stdout.write(f"Начинаю обработку {loads.count()} записей нагрузки...")
        
        # Вызываем наш отдельный сервис
        created_count = generate_planned_lessons_bulk(semester, loads)

        self.stdout.write(
            self.style.SUCCESS(f"Успешно создано {created_count} PlannedLesson(s)")
        )