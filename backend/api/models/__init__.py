"""Пакет для импорта моделей"""

from .buildings import Building, BuildingTravelTime, Classroom, Equipment
from .constraints import (
    BuildingPriority,
    EquipmentRequirement,
    Constraint,
)
from .education_subjects import (
    Institute,
    StudyGroup,
    StudyProgram,
    Teacher,
    Discipline,
    LessonType,
)
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
    Timeslot,
)
from .academic_load import (
    AcademicLoad,
    Lesson,
    PlannedLesson
)
