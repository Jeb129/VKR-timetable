from .database import (
    AcademicLoadViewSet,
    BookingTypeViewSet,
    BuildingTravelTimeViewSet,
    BuildingViewSet,
    ClassroomPreferenceViewSet,
    ClassroomViewSet,
    ConstraintViewSet,
    DisciplineViewSet,
    EquipmentViewSet,
    InstituteViewSet,
    LessonTypeViewSet,
    LessonViewSet,
    StudyGroupViewSet,
    StudyProgramViewSet,
    TeacherViewSet,
    TimeslotViewSet,
)
from .excel import ExcelAPIView
from .requests import RequestViewSet
from .schedule import (
    ClassroomScheduleView,
    DraftLessonViewSet,
    GroupScheduleView,
    ScheduleScenarioViewSet,
    TeacherScheduleView,
)
from .statistics import BuildingLoadView
from .plannedlessons import PlannedLessonViewSet
from .generation import GenerationViewSet
