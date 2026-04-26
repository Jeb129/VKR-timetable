from django.conf import settings
from django.core.management.base import BaseCommand

from api.services.data_import.excel import import_excel
from api.services.data_import.loaders import AcademicLoadReader
from api.services.data_import.structure import ACADEMIC_LOAD_STRUCTURE


class Command(BaseCommand):
    help = "Заполняет данные из сырого файла нагрузки. Да помилует господь ваши души\n!!!!!!!ИСПОЛЬЗОВАТЬ ТОЛЬКО ДЛЯ ТЕСТ(!!!!!!!"
    def handle(self, *args, **kwargs):
        excel_path = settings.BASE_DIR / "../../Nagruzka.xlsx"
        if not excel_path.exists():
            self.stdout.write(self.style.ERROR("Файл не найден"))
            return
        self.stdout.write(f"Чтение файла....")
        data = import_excel(excel_path,ACADEMIC_LOAD_STRUCTURE)
        self.stdout.write(f"Прочитано строк: {len(data)}")

        # for field in data[15525]:
        #     print(field,field.__class__.__name__)

        load_stream = AcademicLoadReader(data)

        for msg in load_stream:
            match msg.level:
                case "WARNING":
                    self.stdout.write(self.style.WARNING(msg))
                case "ERROR":
                    self.stdout.write(self.style.HTTP_NOT_FOUND(msg))
                case "CRITICAL":
                    self.stdout.write(self.style.NOTICE(msg))


        self.stdout.write()
        self.stdout.write(self.style.SUCCESS(f"Успешно обработано строк {load_stream.success_counter}"))
        self.stdout.write(self.style.WARNING(f"Пропущено строк {load_stream.skipped_counter}"))
        self.stdout.write(self.style.ERROR(f"Строк с ошибками {load_stream.error_counter}"))
                        
        self.stdout.write()
        self.stdout.write(self.style.HTTP_INFO(f"Создано направлений подгатовки: {load_stream.programs_created_counter}"))
        self.stdout.write(self.style.HTTP_INFO(f"Сщздано учебных групп: {load_stream.groups_created_counter}"))
        self.stdout.write(self.style.HTTP_INFO(f"Создано преподавателей: {load_stream.teachers_created_counter}"))
        self.stdout.write(self.style.HTTP_INFO(f"Создано записей нагрузки: {load_stream.load_created_counter}"))
        
        self.stdout.write()
        self.stdout.write(self.style.HTTP_INFO(f"Найдено существующих направлений подгатовки: {load_stream.programs_exists_counter}"))
        self.stdout.write(self.style.HTTP_INFO(f"Найдено существующих учебных групп: {load_stream.groups_exists_counter}"))
        self.stdout.write(self.style.HTTP_INFO(f"Найдено существующих преподавателей: {load_stream.teachers_exists_counter}"))
        self.stdout.write(self.style.HTTP_INFO(f"Найдено существующих записей нагрузки: {load_stream.load_exists_counter}"))




