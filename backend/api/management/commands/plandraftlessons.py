from django.conf import settings
from django.core.management.base import BaseCommand
from django.utils import timezone

from api.models import AcademicLoad
from api.services.data_import.loaders import export_loading
from api.services.schedule.planner import generate_planned_lessons


class Command(BaseCommand):
    help = "Экспорт академической нагрузки в Excel (1NF)."

    # def add_arguments(self, parser):
    #     parser.add_argument("path", type=str, help="Путь к создаваемому XLSX файлу")

    def handle(self, *args, **options):
        loads = AcademicLoad.objects.all()
        # path = options["path"]
        now = timezone.localtime(timezone.now())
        # path = (
        #     settings.DATA_FILES_DIR
        #     / f"план-занятий_{now.strftime("%Y-%m-%d_%H-%M-%S")}.txt"
        # )
        # self.stdout.write(self.style.SUCCESS(f"Файл успешно создан: {path}"))

        result = generate_planned_lessons(loads)

        self.stdout.write(self.style.SUCCESS(f"Запланировано занятий: {len(result)}"))
        for res in result:
            print(res,'\n')

        