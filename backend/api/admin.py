from django.contrib import admin

from api.models import (AcademicLoad, Building, BuildingPriority, Classroom,
                        Constraint, Discipline, Institute, Lesson, LessonType,
                        ScheduleScenario, StudyGroup, StudyProgram, Teacher,
                        Timeslot)

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
    list_display = ("short_name", "institute")
    list_filter = ("institute",)
    inlines = [StudyGroupInline]  # Создаем группы прямо в программе
    search_fields = ("name", "short_name")


@admin.register(StudyGroup)
class StudyGroupAdmin(admin.ModelAdmin):
    list_display = ("name", "stud_program", "students_count", "admission_year")
    search_fields = ("name",)
    list_filter = ("stud_program__institute", "admission_year")
    autocomplete_fields = ["stud_program"]  # Поиск программы по названию


@admin.register(Teacher)
class TeacherAdmin(admin.ModelAdmin):
    list_display = ("name","post", "constraint_weight", "user")
    search_fields = ("name",)


@admin.register(AcademicLoad)
class AcademicLoadAdmin(admin.ModelAdmin):
    list_display = ("study_group", "discipline", "teacher", "whole_hours")
    list_filter = ("study_group__stud_program__institute", "teacher")
    # Это сделает выбор группы и препода удобным (через поиск)
    autocomplete_fields = ["study_group", "teacher", "discipline"]


@admin.register(Lesson)
class LessonAdmin(admin.ModelAdmin):
    list_display = ("discipline", "timeslot", "classroom", "scenario")
    list_filter = ("scenario", "timeslot__day", "classroom__building")
    # Чтобы не грузить сервер огромными списками
    raw_id_fields = ("timeslot", "classroom")


@admin.register(Timeslot)
class TimeslotAdmin(admin.ModelAdmin):
    list_display = ("day", "order_number", "time_start", "time_end", "week_num")
    list_filter = ("day", "week_num")
    ordering = ("week_num", "day", "order_number")


admin.site.register(Discipline, search_fields=["name"])
admin.site.register(LessonType)
admin.site.register(ScheduleScenario)
admin.site.register(BuildingPriority)
admin.site.register(Constraint)
