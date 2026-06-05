from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.translation import gettext_lazy as _

from .forms import CustomUserCreationForm, CustomUserChangeForm
from .models import CustomUser


class CustomUserAdmin(UserAdmin):
    """Настройка отображения пользователя в админ-панели"""
    
    add_form = CustomUserCreationForm
    form = CustomUserChangeForm
    model = CustomUser

    # Поля, которые будут видны в списке пользователей
    list_display = [
        "email", 
        "username", 
        "is_email_verified", 
        "is_internal_view", # Используем метод для отображения свойства
        "is_schedule_moderator", 
        "is_booking_moderator",
        "is_staff"
    ]
    
    # Фильтры справа
    list_filter = ("is_email_verified", "is_schedule_moderator", "is_booking_moderator", "is_staff", "is_superuser")

    fieldsets = (
        (None, {"fields": ("email", "password")}),
        (_("Personal info"), {"fields": ("username", "first_name", "last_name")}),
        (
            _("Права доступа к API"),
            {
                "fields": (
                    "internal_user",
                    "is_email_verified",
                    "is_schedule_moderator",
                    "is_booking_moderator",
                    "moodle_id",
                )
            },
        ),
        (
            _("Привязка"),
            {"fields": ("teacher", "study_group")},
        ),
        (
            _("Пава доступа к системе"),
            {
                "fields": (
                    "is_active",
                    "is_staff",
                    "is_superuser",
                    "groups",
                    "user_permissions",
                ),
            },
        ),
        (_("Important dates"), {"fields": ("last_login", "date_joined")}),
    )

    # Поля при создании нового пользователя
    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": ("email", "password", "username"),
            },
        ),
    )

    # Поля только для чтения
    readonly_fields = ("is_internal_view",)

    def is_internal_view(self, obj):
        """Отображение свойства is_internal в списке (с иконкой)"""
        return obj.is_internal
    
    is_internal_view.boolean = True # Рисует галочку/крестик в админке
    is_internal_view.short_description = "Internal Status"

    ordering = ("email",)


admin.site.register(CustomUser, CustomUserAdmin)