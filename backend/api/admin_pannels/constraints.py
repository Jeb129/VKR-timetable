from django.contrib import admin
from import_export import fields, resources
from import_export.admin import ImportExportModelAdmin
from import_export.widgets import ForeignKeyWidget

from api.models import (Building, BuildingPriority, BuildingTravelTime,
                        Constraint, Discipline, Equipment,
                        EquipmentRequirement, Institute, LessonType)

# Ресурсы


class EquipmentRequirementResource(resources.ModelResource):
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
    equipment = fields.Field(
        column_name="оборудование",
        attribute="equipment",
        widget=ForeignKeyWidget(Equipment, "name"),
    )

    class Meta:
        model = EquipmentRequirement
        fields = ("id", "discipline", "lesson_type", "equipment")
        import_id_fields = ("id",)


class BuildingTravelTimeResource(resources.ModelResource):
    from_building = fields.Field(
        column_name="из_корпуса",
        attribute="from_building",
        widget=ForeignKeyWidget(Building, "short_name"),
    )
    to_building = fields.Field(
        column_name="в_корпус",
        attribute="to_building",
        widget=ForeignKeyWidget(Building, "short_name"),
    )

    class Meta:
        model = BuildingTravelTime
        fields = ("id", "from_building", "to_building", "travel_time_minutes")
        import_id_fields = ("id",)


class BuildingPriorityResource(resources.ModelResource):
    institute = fields.Field(
        column_name="институт",
        attribute="institute",
        widget=ForeignKeyWidget(Institute, "short_name"),
    )
    building = fields.Field(
        column_name="корпус",
        attribute="building",
        widget=ForeignKeyWidget(Building, "short_name"),
    )

    class Meta:
        model = BuildingPriority
        fields = ("id", "institute", "building", "weight")
        import_id_fields = ("id",)


@admin.register(Constraint)
class ConstraintAdmin(admin.ModelAdmin):

    list_display = (
        "description",
        "name",
        "is_active",
        "weight",
        "is_hard",
        "manual_only",
        "generation_only",
    )
    list_editable = ("weight", "is_active", "is_hard", "manual_only", "generation_only")
    search_fields = ("name", "description")
    list_filter = ("is_active", "is_hard")

    fieldsets = (
        (None, {"fields": ("description", "name")}),
        ("Настройки веса", {"fields": (("weight", "is_hard"),)}),
        (
            "Область применения",
            {
                "fields": ("is_active", "manual_only", "generation_only"),
                "description": "Настройте, где и как будет проверяться это ограничение",
            },
        ),
    )


@admin.register(EquipmentRequirement)
class EquipmentRequirementAdmin(ImportExportModelAdmin):

    resource_class = EquipmentRequirementResource
    list_display = ("discipline", "lesson_type", "equipment")
    list_filter = ("lesson_type", "equipment", "discipline")
    search_fields = ("discipline__name", "equipment__name")
    autocomplete_fields = ["discipline", "lesson_type", "equipment"]


@admin.register(BuildingPriority)
class BuildingPriorityAdmin(ImportExportModelAdmin):

    resource_class = BuildingPriorityResource
    list_display = ("institute", "building", "weight")
    list_editable = ("weight",)
    list_filter = ("institute", "building")
    autocomplete_fields = ["institute", "building"]


@admin.register(BuildingTravelTime)
class BuildingTravelTimeAdmin(ImportExportModelAdmin):

    resource_class = BuildingTravelTimeResource
    list_display = ("from_building", "to_building", "travel_time_minutes")
    list_editable = ("travel_time_minutes",)
    list_filter = ("from_building", "to_building")
    autocomplete_fields = ["from_building", "to_building"]
