from django.contrib import admin
from django.shortcuts import redirect
from django.utils.html import format_html
from import_export import fields, resources
from import_export.admin import ImportExportModelAdmin
from import_export.widgets import DateTimeWidget, ForeignKeyWidget

from api.models import (Booking, BookingType, Classroom, ClassroomPreference,
                        Discipline, ExcludedTimeslot, LessonType, Request,
                        ScheduleAdjustment, Teacher, Timeslot, enums)
from authentification.models import CustomUser


# --- Исключения времени ---
class ExcludedTimeslotResource(resources.ModelResource):
    user = fields.Field(
        column_name="пользователь",
        attribute="user",
        widget=ForeignKeyWidget(CustomUser, "username"),
    )
    teacher = fields.Field(
        column_name="преподаватель",
        attribute="teacher",
        widget=ForeignKeyWidget(Teacher, "name"),
    )
    timeslot = fields.Field(
        column_name="таймслот_id", attribute="timeslot"
    )  # Тут лучше оставить ID или настроить сложный виджет

    class Meta:
        model = ExcludedTimeslot
        fields = ("id", "user", "status", "teacher", "timeslot", "description")


# --- Предпочтения по аудиториям ---
class ClassroomPreferenceResource(resources.ModelResource):
    user = fields.Field(
        column_name="пользователь",
        attribute="user",
        widget=ForeignKeyWidget(CustomUser, "username"),
    )
    teacher = fields.Field(
        column_name="преподаватель",
        attribute="teacher",
        widget=ForeignKeyWidget(Teacher, "name"),
    )
    discipline = fields.Field(
        column_name="дисциплина",
        attribute="discipline",
        widget=ForeignKeyWidget(Discipline, "name"),
    )
    classroom = fields.Field(
        column_name="аудитория",
        attribute="classroom",
        widget=ForeignKeyWidget(Classroom, "name"),
    )

    class Meta:
        model = ClassroomPreference
        fields = (
            "id",
            "user",
            "status",
            "teacher",
            "discipline",
            "classroom",
            "description",
        )


# --- Бронирования ---
class BookingResource(resources.ModelResource):
    user = fields.Field(
        column_name="пользователь",
        attribute="user",
        widget=ForeignKeyWidget(CustomUser, "username"),
    )
    classroom = fields.Field(
        column_name="аудитория",
        attribute="classroom",
        widget=ForeignKeyWidget(Classroom, "name"),
    )
    booking_type = fields.Field(
        column_name="тип_брони",
        attribute="booking_type",
        widget=ForeignKeyWidget(BookingType, "name"),
    )

    class Meta:
        model = Booking
        fields = (
            "id",
            "user",
            "status",
            "classroom",
            "booking_type",
            "date_start",
            "date_end",
            "description",
        )


class ScheduleAdjustmentRequest(Request):
    """Proxy-модель для разделения логики в админке"""

    class Meta:
        proxy = True
        verbose_name = "заявка на изменение расписания"
        verbose_name_plural = "заявки на изменения расписания"


# Инлайны


class ScheduleAdjustmentInline(admin.TabularInline):
    model = ScheduleAdjustment
    extra = 1
    autocomplete_fields = ["lesson", "timeslot", "classroom"]
    fields = ("date", "lesson", "timeslot", "classroom")


# Панели


class BaseRequestAdmin(admin.ModelAdmin):
    """Базовый класс для всех типов заявок"""

    list_display = ("id", "display_status", "user", "type", "created_at")
    list_filter = ("status", "type", "created_at")
    search_fields = ("user__username", "description")
    readonly_fields = ("created_at","type")
    actions = ["approve_requests", "reject_requests"]

    @admin.action(description="Одобрить выбранные заявки")
    def approve_requests(self, request, queryset):
        queryset.update(status=enums.RequestStatus.VERIFIED)

    @admin.action(description="Отклонить выбранные заявки")
    def reject_requests(self, request, queryset):
        queryset.update(status=enums.RequestStatus.REJECTED)

    def display_status(self, obj):
        colors = {
            enums.RequestStatus.PENDING: "orange",
            enums.RequestStatus.VERIFIED: "green",
            enums.RequestStatus.REJECTED: "red",
            enums.RequestStatus.CANCELED: "gray",
        }
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            colors.get(obj.status, "black"),
            obj.get_status_display(),
        )

    display_status.short_description = "Статус"

    def get_readonly_fields(self, request, obj=None):
        # Если объект уже создан, запрещаем менять тип и пользователя
        if obj:
            return self.readonly_fields + ("type", "user")
        return self.readonly_fields


@admin.register(ExcludedTimeslot)
class ExcludedTimeslotAdmin(ImportExportModelAdmin, BaseRequestAdmin):
    fields = ("status", "user", "teacher", "timeslot", "description", "admin_comment")
    autocomplete_fields = ["teacher", "timeslot", "user"]


@admin.register(ClassroomPreference)
class ClassroomPreferenceAdmin(ImportExportModelAdmin, BaseRequestAdmin):
    fields = (
        "status",
        "user",
        "teacher",
        "discipline",
        "lesson_type",
        "classroom",
        "description",
        "admin_comment",
    )
    autocomplete_fields = ["teacher", "discipline", "lesson_type", "classroom", "user"]


@admin.register(Booking)
class BookingAdmin(ImportExportModelAdmin, BaseRequestAdmin):
    resource_class = BookingResource
    list_display = (
        "display_status",
        "classroom",
        "booking_type",
        "date_start",
        "date_end",
    )
    fields = (
        "status",
        "user",
        "classroom",
        "booking_type",
        ("date_start", "date_end"),
        "description",
        "admin_comment",
    )
    autocomplete_fields = ["classroom", "booking_type", "user"]


@admin.register(ScheduleAdjustmentRequest)
class ScheduleAdjustmentRequestAdmin(BaseRequestAdmin):
    """
    Специальная админка для заявок типа SCHEDULE_ADJUSTMENT.
    """
    # readonly_fields = ("type",)
    inlines = [ScheduleAdjustmentInline]

    def get_queryset(self, request):
        return (
            super()
            .get_queryset(request)
            .filter(type=enums.RequestType.SCHEDULE_ADJUSTMENT)
        )

    def save_model(self, request, obj, form, change):
        # Принудительно ставим тип при создании через эту панель
        if not obj.pk:
            obj.type = enums.RequestType.SCHEDULE_ADJUSTMENT
        super().save_model(request, obj, form, change)


@admin.register(BookingType)
class BookingTypeAdmin(admin.ModelAdmin):
    search_fields = ("name",)


@admin.register(Request)
class RequestAdmin(BaseRequestAdmin):
    """Общий список всех заявок для модератора"""

    def has_add_permission(self, request):
        return False

    def change_view(self, request, object_id, form_url="", extra_context=None):
        obj = self.get_object(request, object_id)
        if obj:
            if obj.type == enums.RequestType.SCHEDULE_ADJUSTMENT:
                return redirect(
                    f"admin:api_scheduleadjustmentrequest_change", object_id
                )

            for rel in obj._meta.get_all_related_objects():
                if (
                    hasattr(rel, "parent_link")
                    and rel.parent_link
                    and hasattr(obj, rel.get_accessor_name())
                ):
                    model_name = rel.model._meta.model_name
                    return redirect(f"admin:api_{model_name}_change", object_id)

        return super().change_view(request, object_id, form_url, extra_context)
