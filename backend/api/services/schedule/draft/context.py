from contextlib import contextmanager
from api.models import Lesson
from api.services.schedule.draft.manager import DraftLessonManager


@contextmanager
def draft_context(scenario_id, storage):
    """
    Подменяет Lesson._default_manager и Lesson.objects.
    """
    original_base_manager = Lesson.objects
    draft_manager = DraftLessonManager(storage=storage, scenario_id=scenario_id, base_manager = original_base_manager)
    Lesson.objects = draft_manager
    try:
        yield draft_manager,
    finally:
        Lesson.objects = original_base_manager