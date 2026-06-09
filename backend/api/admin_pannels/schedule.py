from django.contrib import admin
from django.db.models import Count
from import_export import fields, resources
from import_export.admin import ImportExportModelAdmin
from import_export.widgets import ForeignKeyWidget, ManyToManyWidget

from api.models import (Classroom, Discipline, Lesson, LessonType,
                        PlannedLesson, ScheduleAdjustment, ScheduleScenario,
                        Semester, StudyGroup, Teacher, Timeslot)

# Ресурсы
# admin.site.register(LessonType)

class ScheduleAdjustmentResource(resources.ModelResource):
    request_user = fields.Field(
        attribute="request__user__username", column_name="от_кого"
    )
    discipline = fields.Field(
        attribute="lesson__discipline__name", column_name="дисциплина"
    )

    class Meta:
        model = ScheduleAdjustment
        fields = ("id", "date", "discipline", "timeslot", "classroom")


class LessonResource(resources.ModelResource):
    scenario = fields.Field(
        column_name="сценарий",
        attribute="scenario",
        widget=ForeignKeyWidget(ScheduleScenario, "name"),
    )
    discipline = fields.Field(
        column_name="дисциплина",
        attribute="discipline",
        widget=ForeignKeyWidget(Discipline, "name"),
    )
    lesson_type = fields.Field(
        column_name="вид_занятия",
        attribute="lesson_type",
        widget=ForeignKeyWidget(LessonType, "name"),
    )
    classroom = fields.Field(
        column_name="аудитория",
        attribute="classroom",
        widget=ForeignKeyWidget(Classroom, "name"),
    )

    # ManyToMany поля через запятую
    teachers = fields.Field(
        column_name="преподаватели",
        attribute="teachers",
        widget=ManyToManyWidget(Teacher, separator=",", field="name"),
    )
    study_groups = fields.Field(
        column_name="группы",
        attribute="study_groups",
        widget=ManyToManyWidget(StudyGroup, separator=",", field="name"),
    )

    class Meta:
        model = Lesson
        fields = (
            "id",
            "scenario",
            "discipline",
            "lesson_type",
            "timeslot",
            "classroom",
            "teachers",
            "study_groups",
            "whole_weeks",
            "priority",
        )
        import_id_fields = ("id",)


class PlannedLessonResource(resources.ModelResource):
    class Meta:
        model = PlannedLesson
        fields = (
            "id",
            "semester",
            "discipline",
            "lesson_type",
            "lessons_in_cycle",
            "whole_weeks",
            "priority",
        )


# Инлайны
# Панели


@admin.register(Semester)
class SemesterAdmin(admin.ModelAdmin):
    list_display = ("name", "date_start", "date_end")
    search_fields = ("name",)


@admin.register(Timeslot)
class TimeslotAdmin(admin.ModelAdmin):
    list_display = ("order_number", "day", "week_num", "time_start", "time_end")
    list_filter = ("day", "week_num")
    ordering = ("week_num", "day", "order_number")
    search_fields = ("order_number",)



@admin.register(ScheduleScenario)
class ScheduleScenarioAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "semester",
        "is_active",
        "generation_status",
        "total_penalty",
    )
    list_filter = ("semester", "is_active")
    actions = ["make_active"]
    search_fields = ("name",)


    @admin.action(description="Сделать выбранный сценарий действующим")
    def make_active(self, request, queryset):
        if queryset.count() != 1:
            self.message_user(request, "Выберите только один сценарий", level="error")
            return

        scenario = queryset.first()
        ScheduleScenario.objects.filter(
            semester=scenario.semester, is_active=True
        ).update(is_active=False)
        scenario.is_active = True
        scenario.save()
        self.message_user(request, f"Сценарий '{scenario.name}' теперь активен")


@admin.register(Lesson)
class LessonAdmin(ImportExportModelAdmin):
    resource_class = LessonResource
    list_display = (
        "id",
        "discipline",
        "lesson_type",
        "get_teachers",
        "get_groups",
        "timeslot",
        "classroom",
    )
    list_filter = (
        "scenario",
        "timeslot__day",
        "timeslot__week_num",
        "classroom__building",
    )
    search_fields = ("discipline__name", "teachers__name", "study_groups__name")
    autocomplete_fields = [
        "scenario",
        "discipline",
        "lesson_type",
        "timeslot",
        "classroom",
    ]
    filter_horizontal = ("teachers", "study_groups")

    def get_teachers(self, obj):
        return ", ".join([t.name for t in obj.teachers.all()])

    get_teachers.short_description = "Преподаватели"

    def get_groups(self, obj):
        return ", ".join([g.name for g in obj.study_groups.all()])

    get_groups.short_description = "Группы"

    def get_queryset(self, request):
        return (
            super()
            .get_queryset(request)
            .prefetch_related(
                "teachers", "study_groups", "discipline", "timeslot", "classroom"
            )
        )


@admin.register(PlannedLesson)
class PlannedLessonAdmin(ImportExportModelAdmin):
    resource_class = PlannedLessonResource

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

    list_filter = ("semester", "lesson_type", "discipline")
    search_fields = ("discipline__name", "study_groups__name", "teachers__name")
    ordering = ("semester", "discipline")
    filter_horizontal = ("study_groups", "teachers")
    raw_id_fields = ("academic_loads",)
    autocomplete_fields = ["semester", "discipline", "lesson_type"]
    actions = ["fast_delete_selected"]

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        queryset = queryset.annotate(
            _loads_count=Count("academic_loads", distinct=True),
            _teachers_count=Count("teachers", distinct=True),
            _groups_count=Count("study_groups", distinct=True),
        )
        return queryset

    @admin.display(description="Нагрузок", ordering="_loads_count")
    def get_loads_count(self, obj):
        return obj._loads_count

    @admin.display(description="Преподавателей", ordering="_teachers_count")
    def get_teachers_count(self, obj):
        return obj._teachers_count

    @admin.display(description="Групп", ordering="_groups_count")
    def get_groups_count(self, obj):
        return obj._groups_count

    @admin.action(description="Быстрое удаление")
    def fast_delete_selected(self, request, queryset):
        count = queryset.count()
        queryset.delete()  # Массовое удаление через SQL
        self.message_user(
            request, f"Успешно удалено {count} записей (включая их связи)."
        )

    def delete_queryset(self, request, queryset):
        queryset.delete()


@admin.register(ScheduleAdjustment)
class ScheduleAdjustmentAdmin(ImportExportModelAdmin):
    resource_class = ScheduleAdjustmentResource
    list_display = ("date", "get_user", "lesson", "timeslot", "get_status")
    list_filter = ("date", "request__status")
    search_fields = ("lesson__discipline__name", "request__user__username")
    autocomplete_fields = ["request", "lesson", "timeslot", "classroom"]

    def get_user(self, obj):
        return obj.request.user

    get_user.short_description = "Пользователь"

    def get_status(self, obj):
        return obj.request.get_status_display()

    get_status.short_description = "Статус заявки"
