from django.db.models import Manager
from django.db.models.sql import Query

from api.models import Lesson
from api.services.schedule.draft.queryset import DraftLessonQuerySet


# class DraftLessonManager(Manager):
#     def __init__(self, storage, scenario_id):
#         super().__init__()
#         self.storage = storage
#         self.scenario_id = scenario_id

#     def get_queryset(self):
#         qs = super().get_queryset()
#         return DraftLessonQuerySet(
#             model=qs.model,
#             query=qs.query.clone(),
#             storage=self.storage,
#             scenario_id=self.scenario_id,
#         )
    
class DraftLessonManager(Manager):
    def __init__(self, storage, scenario_id, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.model = Lesson
        self._storage = storage
        self._scenario_id = scenario_id

    def get_queryset(self):
        return DraftLessonQuerySet(
            model=self.model,
            query=Query(self.model),
            storage=self._storage,
            scenario_id=self._scenario_id,
            using=self._db,
        )