import math

from django.core.management.base import BaseCommand
from api.models import *

class Command(BaseCommand):
    help = "Заполнение сетки времени и базовых ограничений"

    def handle(self, *args, **kwargs):
        semid = 14
        self.stdout.write(
            f"Всего часов в семестре: {sum(AcademicLoad.objects.filter(semester_id=semid).values_list("whole_hours",flat=True))}\n"
            f"Запланировано занятий в семестре: {sum(PlannedLesson.objects.filter(semester_id=semid).values_list("lessons_in_cycle",flat=True))}"
        )
        # any_load = AcademicLoad.objects.get(id=19614)
        # # Математика (плотность занятий)
        # lessons_count = any_load.whole_hours / 2
        # raw_density = (lessons_count / max(any_load.whole_weeks, 1)) * 2

        # # lessons_in_cycle — это ПАРЫ в 2 недели. 
        # # Не может быть больше общего кол-ва пар и не меньше 1 (если есть хоть 1 час)
        # lessons_in_cycle = max(min(math.ceil(raw_density), math.ceil(lessons_count)), 1)

        # # whole_weeks — за сколько недель вычитаем. 
        # # Делим часы на "часы в неделю" (которых ровно lessons_in_cycle штук, т.к. пара=2ч, а цикл=2нед)
        # calculated_weeks = math.ceil(any_load.whole_hours / lessons_in_cycle)

        # self.stdout.write(
        #     f"Проверка записи нагрузки ID:{any_load.id} {any_load.lesson_type} {any_load.discipline}\n"
        #     f"Всего часов: {any_load.whole_hours}\n"
        #     f"Всего недель: {any_load.whole_weeks}\n"
        #     f"lessons_count = {any_load.whole_hours} / 2 = {lessons_count}\n"
        #     f"raw_density = ({lessons_count} / max({any_load.whole_weeks}, 1) [={max(any_load.whole_weeks, 1)}]) * 2 = {raw_density}\n"
        #     f"lessons_in_cycle = max(min(math.ceil({raw_density}), math.ceil({lessons_count})), 1) = {lessons_in_cycle}\n"
        #     f"calculated_weeks = math.ceil({any_load.whole_hours} / {lessons_in_cycle}) = {calculated_weeks}"
        # )