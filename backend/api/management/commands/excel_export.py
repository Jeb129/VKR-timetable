import datetime
from django.conf import settings
from api.services.data_import.excel import export_excel

from django.core.management.base import BaseCommand
from django.utils import timezone
from api.models import AcademicLoad
import pandas as pd

from api.services.data_import.structure import ACADEMIC_LOAD_STRUCTURE


class Command(BaseCommand):
    help = "Экспорт академической нагрузки в Excel (1NF)."

    # def add_arguments(self, parser):
    #     parser.add_argument("path", type=str, help="Путь к создаваемому XLSX файлу")

    def handle(self, *args, **options):
        # path = options["path"]
        now = timezone.now()
        path = settings.BASE_DIR / "data_exports" / f"Нагрузка_{now.date().isoformat()}.xlsx"
        qs = AcademicLoad.objects.select_related(
            "discipline",
            "lesson_type",
            "teacher",
            "study_group",
            "study_group__stud_program",
            "study_group__stud_program__institute",
            "semester",
        ).all()

        data = []

        for load in qs:
            group = load.study_group
            stud_program = group.study_program
            institute = stud_program.institute

            # --- вычисление номера семестра ---
            sem_order = 1 if load.semester.date_start.month < 7 else 0
            sem_year = load.semester.date_start.year - load.study_group.admission_year
            sem_num = sem_year*2 - sem_order + 1

            # Расчет семестра Осень 2022 для 22-ИСбо-1
            # sem_num = 0 (сентябрь 9 месяц)
            # sem_year = 2022 - 2022  = 0
            # sem = 0 * 2 - 0 + 1 = 1

            # Расчет семестра Весна 2023 для 22-ИСбо-1
            # sem_num = 1 (январь 1 месяц)
            # sem_year = 2023 - 2022  = 1
            # sem = 1 * 2 - 1 + 1 = 8

            # Расчет семестра Осень 2025 для 22-ИСбо-1
            # sem_num = 0 (сентябрь 9 месяц)
            # sem_year = 2025 - 2022  = 3
            # sem = 3 * 2 - 0 + 1 = 7

            # Расчет семестра Весна 2026 для 22-ИСбо-1
            # sem_num = 1 (январь 1 месяц)
            # sem_year = 2026 - 2022  = 4
            # sem = 4 * 2 - 1 + 1 = 8
            
            sem_num = (load.semester.date_start.year - load.study_group.admission_year) * 2

            row = [
                # Направление
                institute.short_name,
                stud_program.code,
                stud_program.name,
                stud_program.short_name,

                # Дисциплина
                load.discipline.name,
                load.discipline.allow_merge_teachers,

                # Вид занятия
                load.lesson_type.name,
                load.lesson_type.allow_merge_teachers,
                load.lesson_type.allow_merge_subgroups,
                load.lesson_type.allow_merge_groups,

                # Нагрузка
                sem_num,
                load.control_type,
                load.whole_weeks,
                load.whole_hours,

                # Преподаватель
                load.teacher.name,
                load.teacher.post,

                # Группа
                group.admission_year,
                group.group_num,
                group.sub_group_num,
                group.learning_form,
                group.learning_stage,
                group.students_count,
            ]

            data.append(row)

        export_excel(path, data, ACADEMIC_LOAD_STRUCTURE)
        self.stdout.write(self.style.SUCCESS(f"Файл успешно создан: {path}"))