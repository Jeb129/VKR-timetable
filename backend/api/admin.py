from re import search

from django.contrib import admin
from django.db.models import Count

from api.models import (AcademicLoad, Building, BuildingPriority, Classroom,
                        Constraint, Discipline, Institute, Lesson, LessonType,
                        ScheduleScenario, StudyGroup, StudyProgram, Teacher,
                        Timeslot,Semester,PlannedLesson)

#  ИНЛАЙНЫ (Позволяют создавать связанные объекты на одной странице)


class ClassroomInline(admin.TabularInline):
    model = Classroom
    extra = 3  # Сразу 3 пустых поля для аудиторий


class StudyProgramInline(admin.TabularInline):
    model = StudyProgram
    extra = 1


class StudyGroupInline(admin.TabularInline):
    model = StudyGroup
    extra = 2


@admin.register(Building)
class BuildingAdmin(admin.ModelAdmin):
    list_display = ("name", "address", "work_start_time", "work_end_time")
    inlines = [ClassroomInline]  # Создаем аудитории прямо в корпусе


@admin.register(Institute)
class InstituteAdmin(admin.ModelAdmin):
    list_display = ("short_name", "name")
    inlines = [StudyProgramInline]  # Создаем программы прямо в институте


@admin.register(StudyProgram)
class StudyProgramAdmin(admin.ModelAdmin):
    list_display = ("institute","code","name")
    list_filter = ("institute",)
    inlines = [StudyGroupInline]  # Создаем группы прямо в программе
    search_fields = ("code","name", "short_name")


@admin.register(StudyGroup)
class StudyGroupAdmin(admin.ModelAdmin):
    list_display = ("name", "study_program", "students_count", "admission_year")
    search_fields = ("name",)
    list_filter = ("study_program__institute", "admission_year")
    autocomplete_fields = ["study_program"]  # Поиск программы по названию


@admin.register(Teacher)
class TeacherAdmin(admin.ModelAdmin):
    list_display = ("name","post", "constraint_weight", "user")
    search_fields = ("name",)
    ordering = ("name",)


@admin.register(AcademicLoad)
class AcademicLoadAdmin(admin.ModelAdmin):
    readonly_fields = ["id","semester_order"]
    list_display = ("semester","study_group", "discipline", "lesson_type","teacher", "whole_hours")
    list_filter = ("semester","study_group__study_program__institute", "teacher")
    search_fields = ("id","study_group__study_program__code","study_group__name", "discipline__name", "teacher__name")
    # Это сделает выбор группы и препода удобным (через поиск)
    autocomplete_fields = ["study_group", "teacher", "discipline"]
    # ordering = ["semester__date_start","study_group__name","discipline__name"]
    ordering = ["id"]

    @admin.display(description="Номер семестра")
    def semester_order(self, obj):
        return obj.semester_order



@admin.register(Lesson)
class LessonAdmin(admin.ModelAdmin):
    list_display = ("discipline", "timeslot", "classroom", "scenario")
    list_filter = ("scenario", "timeslot__day", "classroom__building")
    search_fields = ("id","discipline__name")
    # Чтобы не грузить сервер огромными списками
    raw_id_fields = ("timeslot", "classroom")


@admin.register(Timeslot)
class TimeslotAdmin(admin.ModelAdmin):
    list_display = ("day", "order_number", "time_start", "time_end", "week_num")
    list_filter = ("day", "week_num")
    ordering = ("week_num", "day", "order_number")

@admin.register(Semester)
class SemesterAdmin(admin.ModelAdmin):
    list_display = ("name", "date_start", "date_end")
    search_fields = ("name",)
    ordering = ("date_start",)

@admin.register(PlannedLesson)
class PlannedLessonAdmin(admin.ModelAdmin):
    # Поля, отображаемые в списке
    list_display = (
        "id",
        "discipline",
        "lesson_type",
        "semester",
        "get_loads_count",
        "get_teachers_count",
        "get_groups_count",
        "lessons_in_cycle",
        "whole_weeks",
        "priority",
    )

    # Фильтры справа
    list_filter = ("semester", "lesson_type", "discipline")
    
    # Поиск
    search_fields = ("discipline__name", "study_groups__name", "teachers__name")

    # Оптимизация запроса: считаем количество связанных объектов в одном SQL-запросе
    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        queryset = queryset.annotate(
            _loads_count=Count("academic_loads", distinct=True),
            _teachers_count=Count("teachers", distinct=True),
            _groups_count=Count("study_groups", distinct=True),
        )
        return queryset

    # Методы для отображения колонок с поддержкой сортировки
    
    @admin.display(description="Нагрузок", ordering="_loads_count")
    def get_loads_count(self, obj):
        return obj._loads_count

    @admin.display(description="Преподавателей", ordering="_teachers_count")
    def get_teachers_count(self, obj):
        return obj._teachers_count

    @admin.display(description="Групп", ordering="_groups_count")
    def get_groups_count(self, obj):
        return obj._groups_count

    # Настройка формы редактирования (для удобства работы с M2M)
    filter_horizontal = ("study_groups", "teachers", "academic_loads")
    
    # Чтобы не делать лишних запросов при открытии формы редактирования
    raw_id_fields = ("academic_loads",)

    actions = ['fast_delete_selected']

    def get_actions(self, request):
        # Удаляем стандартное удаление, чтобы случайно не запустить "медленный" процесс
        actions = super().get_actions(request)
        if 'delete_selected' in actions:
            del actions['delete_selected']
        return actions

    @admin.action(description="БЫСТРОЕ УДАЛЕНИЕ (без проверки связей)")
    def fast_delete_selected(self, request, queryset: QuerySet):
        # .delete() на уровне QuerySet в Django работает гораздо быстрее,
        # так как он минимизирует работу "коллектора" и делает массовое удаление.
        count = queryset.count()
        queryset.delete()
        self.message_user(request, f"Успешно удалено {count} записей (включая их связи).")

    # Также полезно для массовых операций
    def delete_queryset(self, request, queryset):
        """Переопределение для удаления через контекстное меню действий"""
        queryset.delete()

        
admin.site.register(Discipline, search_fields=["name"])
admin.site.register(LessonType)
admin.site.register(ScheduleScenario)
admin.site.register(BuildingPriority)
admin.site.register(Constraint)
admin.site.register(Classroom)
# admin.site.register(Semester)
