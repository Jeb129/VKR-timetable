from django.conf import settings
from django.core.management.base import BaseCommand
from django.utils import timezone

from api.services.data_import.loaders import export_loading


class Command(BaseCommand):
    help = "Экспорт академической нагрузки в Excel (1NF)."

    # def add_arguments(self, parser):
    #     parser.add_argument("path", type=str, help="Путь к создаваемому XLSX файлу")

    def handle(self, *args, **options):
        # path = options["path"]
        now = timezone.localtime(timezone.now())
        path = (
            settings.BASE_DIR
            / "data_exports"
            / f"manage_Нагрузка_{now.strftime("%Y-%m-%d_%H-%M-%S")}.xlsx"
        )
        export_loading(path)
        self.stdout.write(self.style.SUCCESS(f"Файл успешно создан: {path}"))
