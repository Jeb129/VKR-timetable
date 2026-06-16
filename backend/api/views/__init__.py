from .database import (
    AcademicLoadViewSet,
    BookingTypeViewSet,
    BuildingTravelTimeViewSet,
    BuildingViewSet,
    ClassroomBookingAbleViewSet,
    ClassroomLessonAbleViewSet,
    ClassroomPreferenceViewSet,
    ClassroomViewSet,
    ConstraintViewSet,
    DisciplineViewSet,
    EquipmentViewSet,
    InstituteViewSet,
    LessonTypeViewSet,
    LessonViewSet,
    SemesterViewSet,
    StudyGroupViewSet,
    StudyProgramViewSet,
    TeacherViewSet,
    TimeslotViewSet,
)
from .excel import ExcelAPIView
from .generation import GenerationViewSet
from .plannedlessons import PlannedLessonViewSet
from .requests import RequestViewSet
from .schedule import (ClassroomScheduleView, DraftLessonViewSet,
                       GroupScheduleView, ScheduleScenarioViewSet,
                       TeacherScheduleView)
from .statistics import BuildingLoadView
