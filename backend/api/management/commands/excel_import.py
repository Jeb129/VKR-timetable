import os, sys
from django.core.management.base import BaseCommand
from django.conf import settings

from api.management.commands.raw_import import create_welldone_data
from api.models import *
from api.services.data_import.excel import import_excel

from collections import defaultdict

from api.services.data_import.loaders import import_loading
from api.services.schedule.mapper import get_semester_by_date


class Command(BaseCommand):
    help = "Заполняет данные из сырого файла нагрузки. Да помилует господь ваши души\n!!!!!!!ИСПОЛЬЗОВАТЬ ТОЛЬКО ДЛЯ ТЕСТ(!!!!!!!"
    def handle(self, *args, **kwargs):
        excel_path = settings.BASE_DIR / "../../Nagruzka.xlsx"
        if not excel_path.exists():
            self.stdout.write(self.style.ERROR("Файл не найден"))
            return
        self.stdout.write(f"Чтение файла....")
        data = import_excel(excel_path)
        self.stdout.write(f"Прочитано строк: {len(data)}")
        data = create_welldone_data(data)

        info,created,exists = import_loading(data)
        self.stdout.write(self.style.HTTP_INFO(info))
        self.stdout.write(self.style.SUCCESS(created))
        self.stdout.write(self.style.WARNING(exists))




