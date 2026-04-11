import os, sys
from django.core.management.base import BaseCommand
from django.conf import settings

from api.models import *
from api.services.data_import.excel import import_excel

from collections import defaultdict

from api.services.schedule.mapper import get_semester_by_date


class Command(BaseCommand):
    help = "Заполняет данные из сырого файла нагрузки. Да помилует господь ваши души\n!!!!!!!ИСПОЛЬЗОВАТЬ ТОЛЬКО ДЛЯ ТЕСТ(!!!!!!!"
    def handle(self, *args, **kwargs):
        self.stdout.write("Импорт нагрузки")
        acaddemic_load_path = settings.BASE_DIR / "../../Nagruzka.xlsx"
        if not os.path.exists(acaddemic_load_path):
            self.stdout.write(self.style.WARNING(f"{acaddemic_load_path}: Файл с нагрузкой не найден, пропускаем..."))
        else:
            data = import_excel(acaddemic_load_path)
            print("Прочитано строк: ",len(data))
            preloaded = []
            for idx, d in enumerate(data,start=3):
                sys.stdout.write(f"\rОбработка строки {idx}...")
                sys.stdout.flush()
                if d[18] not in ["Лаб", "Лек", "Пр"]: continue
                if d[8] < 2021: continue

                preloaded.append((
                        # Направление подготовки
                        d[9], # Институт 0
                        d[4], # Шифр 1
                        d[5], # Наименование 2
                        None, # 3

                        # Нагрузка
                        d[12], # Дисциплина 4
                        d[18], # Вид занятия 5
                        d[20], # Контроль 6
                        d[19], # часы 7
                        d[17], # недели 8

                        # Преподаватель
                        d[35], # ФИО 9
                        d[36], # Должность 10

                        # Группв
                        d[8], # Год поступления 11
                        str(d[15]).split(sep="-")[2] if "-" in d[15] else None , # Номер группы 12
                        str(d[11]).split("п/г ")[1][0] if "п/г" in str(d[11]) else None, # номер подгруппы 13
                        d[54], # Форма 14
                        d[53], # Уровень 15
                        d[16], # кол-во студентов 16


                        d[14] # Семестр и курс (для нагрузки) 17
                        ))
            print()
            
            # teachers = {((str(p[9]).strip(), str(p[10]).strip()) if p[9] else None) for p in preloaded}
            teachers = {(p[0],p[9],p[10]) for p in preloaded}
            study_programs = {(p[0],p[1], p[2]) for p in preloaded}
            study_groups = {(p[1], p[11],p[12], p[13], p[14], p[15],p[16]) for p in preloaded}
            load = {(p[4],p[5],p[6],p[7],p[8]) for p in preloaded}

            counter = defaultdict(int)
            for (i, n, p) in teachers:
                if n.__class__ is float: continue 
                counter[n] += 1
                if counter[n] > 1: continue

                institute = Institute.objects.filter(short_name=i).first()
                if not institute:
                    self.stdout.write(self.style.WARNING(f"Не найден институт {i}, преподаватель {n} не будет привязан к институту"))

                Teacher.objects.get_or_create(
                    institute = institute,
                    name = n,
                    post = p,
                )
            
            counter = defaultdict(int)
            for (i, c, n) in study_programs:
                if i.__class__ is float: continue 
                if c.__class__ is float: continue 
                if n.__class__ is float: continue
                
                c, n = str(c), str(n)
                c = c[:-1] if c.endswith(".") else c

                institute = Institute.objects.filter(short_name=i).first()
                if not institute:
                    self.stdout.write(self.style.ERROR(f"Не найден институт {i}, направление {c} {n} пропущено"))
                    continue
                try:
                    StudyProgram.objects.get_or_create(
                        institute = institute,
                        code = c,
                        name=n
                    )
                except Exception as err:
                    self.stdout.write(self.style.ERROR(f"Ошмбка при создании направления {c} {n}:\n{err}"))

            
            for (sp,y,num,sub_num,lf,ls,sc) in study_groups:
                
                sp = str(sp)
                sp = sp[:-1] if c.endswith(".") else sp

                s_prog = StudyProgram.objects.filter(code=sp).first()
                if not s_prog:
                    self.stdout.write(self.style.ERROR(f"Не найдено напрваление {sp}, Група с этим направлением пропущено"))
                    continue

                group, _ = StudyGroup.objects.get_or_create(
                    admission_year = y,
                    stud_program = s_prog,
                    learning_form = lf,
                    learning_stage = ls,
                    group_num=num,
                    sub_group_num = sub_num,
                    students_count = sc
                )
                if sub_num is not None:
                    subs = StudyGroup.objects.filter(
                        admission_year = y,
                        stud_program = s_prog,
                        learning_form = lf,
                        learning_stage = ls,
                        group_num=num,
                    ).values_list("id",flat=True)
                    group.sub_groups.set(list(subs))
        
            for p in preloaded:

                sp = p[1][:-1] if str(p[1]).endswith('.') else str(p[1])
                year = p[11]
                sem_num = int(str(p[17]).split("/")[1])

                sem_data = f"{year + sem_num // 2}-{10 if sem_num % 2 == 1 else 3}-01"
                sem = get_semester_by_date(sem_data)
                if not sem:
                    self.stdout.write(self.style.WARNING(f"Не найден семестр на дату {sem_data}, Запись учебной нагрузки не будет создана"))
                    continue

                program = StudyProgram.objects.filter(code=sp).first()
                
                discipline,_ = Discipline.objects.get_or_create(name=p[4])
                lt,_ = LessonType.objects.get_or_create(name=p[5])
                t = Teacher.objects.filter(name=p[9]).first()

                group = StudyGroup.objects.filter(
                    admission_year = year,
                    stud_program = program,
                    learning_form = p[14],
                    learning_stage = p[15],
                    group_num = p[12],
                    sub_group_num = p[13]
                ).first()
                try:
                    AcademicLoad.objects.get_or_create(
                        semester=sem,
                        discipline=discipline,
                        lesson_type_id=lt.id,
                        teacher=t,
                        study_group=group,
                        whole_hours = p[7],
                        whole_weeks = p[8],
                    )
                except Exception as err:
                    self.stdout.write(self.style.ERROR(f"Ошмбка при создании нагрузки:\n{err}"))


            


