from django.contrib import admin
from import_export import fields, resources
from import_export.admin import ImportExportModelAdmin
from import_export.widgets import ForeignKeyWidget, ManyToManyWidget

from api.models import (Building, BuildingPriority, BuildingTravelTime,
                        Classroom, Equipment, Institute)


# Ресурсы (для импорта данных)

class BuildingResources(resources.ModelResource):
    class Meta:
        model = Building
        fields = ("id", "name","short_name","address","ymap_key","work_start_time","work_end_time")
        import_id_fields = ("id",)
        export_order = ("id", "name")


class EquipmentResource(resources.ModelResource):
    class Meta:
        model = Equipment
        fields = ("id", "name")
        import_id_fields = ("id",)
        export_order = ("id", "name")


class ClassroomResource(resources.ModelResource):
    building = fields.Field(
        column_name="корпус",
        attribute="building",
        widget=ForeignKeyWidget(Building, "short_name"),
    )
    equipment = fields.Field(
        column_name="оборудование",
        attribute="equipment",
        widget=ManyToManyWidget(Equipment, separator=",", field="name"),
    )

    class Meta:
        model = Classroom
        fields = (
            "id",
            "building",
            "num",
            "name",
            "capacity",
            "equipment",
            "allow_lessons",
            "is_virtual",
        )
        import_id_fields = ("id",)


# Инлайны


class ClassroomInline(admin.TabularInline):

    model = Classroom
    extra = 1
    fields = ("num", "capacity", "allow_lessons")
    show_change_link = True  # Ссылка на полную страницу аудитории


class TravelTimeInline(admin.TabularInline):

    model = BuildingTravelTime
    fk_name = "from_building"
    extra = 1


class BuildingPriorityInline(admin.TabularInline):
    model = BuildingPriority
    extra = 1
    autocomplete_fields = ["building"]


# Панели


@admin.register(Building)
class BuildingAdmin(ImportExportModelAdmin):
    resource_class = BuildingResources
    list_display = ("short_name", "name", "work_start_time", "work_end_time")
    search_fields = ("short_name", "name")
    inlines = [ClassroomInline, TravelTimeInline]
    fieldsets = (
        (None, {"fields": (("name", "short_name"), "address", "ymap_key")}),
        ("Режим работы", {"fields": (("work_start_time", "work_end_time"),)}),
    )


@admin.register(Classroom)
class ClassroomAdmin(ImportExportModelAdmin):

    resource_class = ClassroomResource
    list_display = ("num", "building", "capacity", "allow_lessons", "is_virtual")
    list_filter = ("building", "allow_lessons", "is_virtual", "equipment")
    search_fields = ("num", "name", "building__short_name")
    filter_horizontal = ("equipment",)
    autocomplete_fields = ["building"]  # Нужно добавить search_fields в BuildingAdmin


@admin.register(Equipment)
class EquipmentAdmin(ImportExportModelAdmin):

    resource_class = EquipmentResource
    list_display = ("name",)
    search_fields = ("name",)


@admin.register(Institute)
class InstituteAdmin(admin.ModelAdmin):

    list_display = ("short_name", "name")
    search_fields = ("short_name", "name")
    inlines = [BuildingPriorityInline]
