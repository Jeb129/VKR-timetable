from django.core.management.base import BaseCommand
from django.db.models import Count, F
from api.models.academic_load import Lesson
from collections import defaultdict


class Command(BaseCommand):
    help = "Сбор статистики распределения занятий институтов по корпусам"

    def handle(self, *args, **options):
        # 1. Получаем данные по занятиям
        # Мы фильтруем только по активному сценарию, чтобы не мешать данные черновиков.
        # Используем distinct=True в Count, так как ManyToMany с группами может дублировать строки в SQL
        
        raw_data = (
            Lesson.objects.filter(scenario__is_active=True)
            .annotate(
                inst_name=F('study_groups__study_program__institute__short_name'),
                bld_name=F('classroom__building__short_name')
            )
            .values('inst_name', 'bld_name')
            .annotate(lesson_count=Count('id', distinct=True))
            .order_by('inst_name', 'bld_name')
        )

        # 2. Агрегируем данные в Python для расчета итогов
        # Структура: stats[институт][корпус] = количество
        stats = defaultdict(lambda: defaultdict(int))
        institute_totals = defaultdict(int)

        for entry in raw_data:
            inst = entry['inst_name'] or "Не указан"
            building = entry['bld_name'] or "Без корпуса"
            count = entry['lesson_count']
            
            stats[inst][building] += count
            institute_totals[inst] += count

        # 3. Вывод таблицы
        header = f"{'Институт':<20} | {'Корпус':<15} | {'Занятий':<10} | {'Всего':<10} | {'Приоритет (%)'}"
        self.stdout.write(self.style.SUCCESS(header))
        self.stdout.write("-" * len(header))

        for inst, buildings in stats.items():
            total = institute_totals[inst]
            # Сортируем корпуса по убыванию количества занятий
            sorted_buildings = sorted(buildings.items(), key=lambda x: x[1], reverse=True)
            
            for bld, count in sorted_buildings:
                priority = (count / total) * 100
                row = f"{inst:<20} | {bld:<15} | {count:<10} | {total:<10} | {priority:>5.2f}%"
                self.stdout.write(row)
            
            self.stdout.write("-" * len(header))