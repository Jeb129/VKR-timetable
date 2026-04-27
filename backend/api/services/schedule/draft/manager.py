from django.db.models import Manager

from api.models import Lesson
from api.services.schedule.draft.queryset import DraftLessonQuerySet

class DraftLessonManager(Manager):
    def __init__(self, storage, scenario_id, base_manager, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.model = Lesson
        self._storage = storage
        self._scenario_id = scenario_id
        self._base_manager = base_manager

    def get_queryset(self):
        return DraftLessonQuerySet(
            model=self.model,
            storage=self._storage,
            scenario_id=self._scenario_id,
        )