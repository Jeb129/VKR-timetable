from django.contrib import admin
from .models.models import (
    Building, Classroom, Institute, StudyGroup, 
    Teacher, Lesson, ScheduleScenario, AcademicLoad
)

@admin.register(Building)
class BuildingAdmin(admin.ModelAdmin):
    list_display = ('name', 'address')

@admin.register(Classroom)
class ClassroomAdmin(admin.ModelAdmin):
    list_display = ('num', 'building', 'capacity')

@admin.register(ScheduleScenario)
class ScenarioAdmin(admin.ModelAdmin):
    list_display = ('name', 'is_active', 'total_penalty')

admin.site.register(Institute)
admin.site.register(StudyGroup)
admin.site.register(Teacher)
admin.site.register(Lesson)
admin.site.register(AcademicLoad)