from dataclasses import dataclass
from django.contrib import admin, messages
from django.shortcuts import redirect, render
from django.urls import path
from django.utils.html import format_html
from django.core.management import call_command
from django.db import models

from api.models.constraints import Constraint

# 1. Описание структуры команды
@dataclass
class SystemAction:
    id: str
    label: str
    description: str
    button_text: str = "Запустить"
    color: str = "#417690"

# 2. Список объектов (Единственное место для редактирования)
SYSTEM_COMMANDS = [
    SystemAction(
        id='setup_infra',
        label='Инициализация инфраструктуры',
        description='Создание базовых таймслотов и типов занятий по умолчанию.',
        color='#417690'
    ),
    SystemAction(
        id='generate_schedule',
        label='Генератор расписания',
        description='Запуск основного алгоритма распределения занятий.',
        button_text='Начать расчет',
        color='#28a745'
    ),
    SystemAction(
        id='clear_old_scenarios',
        label='Очистка сценариев',
        description='Удаление всех неактивных черновиков расписания.',
        button_text='Очистить',
        color='#dc3545'
    ),
]

# 3. Модель-пустышка
class SystemTask(Constraint):
    class Meta:
        verbose_name = "Инструмент управления"
        verbose_name_plural = "ПУЛЬТ УПРАВЛЕНИЯ"  # "0." выведет модель в топ списка
        proxy = True

# 4. Админка
@admin.register(SystemTask)
class SystemTaskAdmin(admin.ModelAdmin):
    list_display = ('label', 'description', 'run_button')

    def changelist_view(self, request, extra_context=None):
        # Мы полностью заменяем логику "Таблицы из БД" на наш список
        extra_context = extra_context or {}
        extra_context['title'] = 'Пульт управления системой'
        extra_context['system_commands'] = SYSTEM_COMMANDS
        # Используем свой маленький шаблон (код ниже)
        return render(request, 'admin/system_control_panel.html', extra_context)
    
    def label(self, obj): return obj.label
    label.short_description = 'Действие'

    def description(self, obj): return obj.description
    description.short_description = 'Описание'

    def run_button(self, obj):
        return format_html(
            '<a class="button" style="background-color: {}; color: white; padding: 5px 15px;" '
            'href="run/{}/">{}</a>',
            obj.color, obj.id, obj.button_text
        )
    run_button.short_description = 'Управление'

    def get_queryset(self, request):
        # Возвращаем список объектов вместо QuerySet
        return SYSTEM_COMMANDS

    def get_urls(self):
        urls = super().get_urls()
        return [path('run/<str:cmd_id>/', self.admin_site.admin_view(self.handle_run))] + urls

    def handle_run(self, request, cmd_id):
        # Ищем объект в списке по id
        action = next((item for item in SYSTEM_COMMANDS if item.id == cmd_id), None)
        if action:
            try:
                call_command(action.id)
                self.message_user(request, f"Выполнено: {action.label}", messages.SUCCESS)
            except Exception as e:
                self.message_user(request, f"Ошибка: {e}", messages.ERROR)
        return redirect('admin:api_systemtask_changelist')

    def has_add_permission(self, request): return False
    def has_delete_permission(self, request, obj=None): return False