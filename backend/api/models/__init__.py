"""Пакет для импорта моделей"""

from .buildings import Building, BuildingTravelTime, Classroom, Equipment
from .constraints import (
    AcademicLoad,
    BuildingPriority,
    EquipmentRequirement,
    Constraint,
)
from .groups import Institute, StudyGroup, StudyProgram
from .models import Teacher
from .requests import (
    Request,
    ExcludedTimeslot,
    ClassroomPreference,
    ScheduleAdjustment,
    Booking,
)
from .schedule import (
    ScheduleScenario,
    Semester,
    Discipline,
    LessonType,
    Timeslot,
    Lesson,
)
