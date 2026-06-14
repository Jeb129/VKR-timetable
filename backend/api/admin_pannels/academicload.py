from django.contrib import admin
from import_export import fields, resources
from import_export.admin import ImportExportModelAdmin
from import_export.widgets import ForeignKeyWidget

from api.models import (AcademicLoad, Discipline, EquipmentRequirement,
                        Institute, LessonType, StudyGroup, StudyProgram,
                        Teacher)

class TeacherResource(resources.ModelResource):
    institute = fields.Field(
        column_name="институт",
        attribute="institute",
        widget=ForeignKeyWidget(Institute, "short_name"),
    )

    class Meta:
        model = Teacher
        fields = (
            "id",
            "name",
            "institute",
            "post",
            "max_hours_per_week",
            "max_hours_per_day",
        )
        import_id_fields = ("id",)


class StudyGroupResource(resources.ModelResource):
    study_program = fields.Field(
        column_name="направление",
        attribute="study_program",
        widget=ForeignKeyWidget(StudyProgram, "code"),
    )

    class Meta:
        model = StudyGroup
        fields = (
            "id",
            "name",
            "admission_year",
            "study_program",
            "learning_form",
            "learning_stage",
            "group_num",
            "students_count",
        )
        import_id_fields = ("id",)


class AcademicLoadResource(resources.ModelResource):
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
    teacher = fields.Field(
        column_name="преподаватель",
        attribute="teacher",
        widget=ForeignKeyWidget(Teacher, "name"),
    )
    study_group = fields.Field(
        column_name="группа",
        attribute="study_group",
        widget=ForeignKeyWidget(StudyGroup, "name"),
    )

    class Meta:
        model = AcademicLoad
        fields = (
            "id",
            "discipline",
            "lesson_type",
            "teacher",
            "study_group",
            "whole_hours",
            "whole_weeks",
            "semester",
        )
        import_id_fields = ("id",)


# Инлайны


class EquipmentRequirementInline(admin.TabularInline):
    model = EquipmentRequirement
    extra = 1


# Панели


@admin.register(Teacher)
class TeacherAdmin(ImportExportModelAdmin):
    resource_class = TeacherResource
    list_display = ("name", "institute", "post", "max_hours_per_week")
    list_filter = ("institute", "post")
    search_fields = ("name",)
    autocomplete_fields = ["institute"]


@admin.register(StudyProgram)
class StudyProgramAdmin(admin.ModelAdmin):
    list_display = ("code", "short_name", "institute")
    search_fields = ("code", "name", "short_name")
    autocomplete_fields = ["institute"]


@admin.register(StudyGroup)
class StudyGroupAdmin(ImportExportModelAdmin):
    resource_class = StudyGroupResource
    list_display = ("name", "study_program", "admission_year", "students_count")
    list_filter = ("admission_year", "learning_form", "learning_stage", "study_program")
    search_fields = ("name",)
    autocomplete_fields = ["study_program"]


@admin.register(Discipline)
class DisciplineAdmin(admin.ModelAdmin):
    list_display = ("name", "allow_merge_teachers")
    search_fields = ("name",)
    inlines = [EquipmentRequirementInline]


@admin.register(LessonType)
class LessonTypeAdmin(admin.ModelAdmin):
    list_display = ("name", "short_name", "allow_merge_groups", "allow_merge_subgroups")
    search_fields = ("name", "short_name")


@admin.register(AcademicLoad)
class AcademicLoadAdmin(ImportExportModelAdmin):
    resource_class = AcademicLoadResource
    list_display = (
        "semester",
        "study_group",
        "discipline",
        "lesson_type",
        "teacher",
        "whole_hours",
        "whole_weeks",
    )
    list_filter = ("semester", "lesson_type", "study_group__admission_year")
    search_fields = ("study_group__name", "teacher__name", "discipline__name")
    autocomplete_fields = [
        "discipline",
        "lesson_type",
        "teacher",
        "study_group",
        "semester",
    ]

    list_editable = ("whole_hours","whole_weeks")
    actions = ["fast_delete_selected"]

    @admin.action(description="Быстрое удаление")
    def fast_delete_selected(self, request, queryset):
        count = queryset.count()
        queryset.delete()  # Массовое удаление через SQL
        self.message_user(
            request, f"Успешно удалено {count} записей (включая их связи)."
        )
