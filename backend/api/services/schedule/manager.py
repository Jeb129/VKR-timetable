import logging
from typing import List, Optional

from django.db.models import ManyToManyField

from api.models import Lesson
from api.services.constraints import ConstraintManager
from api.services.schedule.context import ScheduleContext
from api.services.constraints.meta import LessonError
from api.services.drafts.storage import ScheduleDraftStorage
from api.services.drafts.commit import commit_lesson, commit_scenario
from api.services.drafts.context import draft_context
from authentification.models import CustomUser

logger = logging.getLogger("constraints")

class ScheduleManager:
    """Класс, управляющий расписанием и проверками"""

    def __init__(self, scenario_id: int, user: CustomUser):
        self.scenario_id = scenario_id
        self.user = user
        self.storage = ScheduleDraftStorage(scenario_id=scenario_id, user_id=user.id)
        self.constraints = ConstraintManager()

        self.context: Optional[ScheduleContext] = None

    def _check_lesson_scenario(self, lesson=None, lesson_id=None):
        """
        Улучшенная проверка: сначала ищем в контексте (в памяти), 
        и только если контекста нет или объект не найден - идем в БД.
        """
        if lesson is None:
            if lesson_id is None:
                raise ValueError("Не передана информация о занятии")
            
            # Пытаемся найти объект в уже загруженном контексте
            if self.context:
                lesson = self.context.get_by_id(lesson_id)
            
            # Если в контексте нет или контекст еще не собран - идем в БД
            if lesson is None:
                lesson = Lesson._default_manager.get(id=lesson_id)
        
        if lesson.scenario_id != self.scenario_id:
            raise ValueError("Занятие не является частью текущего сценария")
        
        return lesson
    

    def build_context(self,*,draft = False):
        if draft:
            with draft_context(self.scenario_id, self.storage):
                self.context = ScheduleContext(self.scenario_id)
        else:
            self.context = ScheduleContext(self.scenario_id)
        return self


    def check_lesson(self, lesson):
        """Проверка занятия по всем ограничениям"""
        # Проверяем наличие индексированного списка занятий. Если нет - индексируем данные из БД
        if self.context is None:
            self.build_context()
    
        errors = self.constraints.check(
            lesson=lesson,
            context=self.context,
            generation_only=False
        )
        
        return LessonError(lesson,errors if errors else None )


    def check_scenario(self) -> List[LessonError] :
        """Проверяет все занятия в сценарии"""
        errors = []
        for lesson in self.context.lessons:
            errors.extend(self.check_lesson(lesson))
        return errors

    def check_lesson_draft(self, lesson_id,*,build_context=False):
        """Проверяет занятия в черновом контексте."""
        if build_context:
            self.build_context(draft=True)
        elif self.context is None:
            raise ValueError("Не собран контекст проверки. Вызовите ScheduleManager.build_context() или передайте build_context=True при вызове метода check_lesson_draft")
        lesson = self.context.get_by_id(lesson_id)
        # if str(lesson_id) == "3021": print(LessonReadSerializer(lesson).data)

        return self.check_lesson(lesson)

    def check_scenario_draft(self,*,build_context=False)-> List[LessonError]:
        """Проверяет весь сценарий в черновом контексте."""
        if build_context:
            self.build_context(draft=True)
        elif self.context is None:
            raise ValueError("Не собран контекст проверки. Вызовите ScheduleManager.build_context() или передайте build_context=True при вызове метода check_scenario_draft")
        return self.check_scenario(self.scenario_id)


        
    # CRUD над черновиками занятий
    def create_lesson_draft(self,data):
        self.context = None
        return self.storage.create_object(data=data)

    def get_lessons_draft(self,*args,**kwargs):
        """Поиск в контексте"""
        if self.context is None:
            raise ValueError("Не собран контекст поиска. Вызовите ScheduleManager.build_context() перед вызовом метода get_lessons_draft")
        return self.context.filter(*args,**kwargs)
    
    def update_lesson_draft(self,lesson_id, diff_data):
        """Вносит изменения в черновик расписания"""
        if lesson_id in self.storage.get_created():
            # если занятие - созданный черновик, то пересоздаем
            self.storage.create_object(data=diff_data,nes_id=lesson_id)
        
        # Получаем оригинальное занятие
        original = Lesson._default_manager.prefetch_related('teachers', 'study_groups').get(id=lesson_id)
        self._check_lesson_scenario(lesson=original)
        
        # Собираем все хранящиеся и входящие изменения в один список
        merged_candidate = {
            **self.storage.get_updated().get(lesson_id, {}), 
            **diff_data}
        # if str(lesson_id) == "3021": print(merged_candidate)
        # Сравниваем все изменения с оригинальным занятием
        final_diff = {}
        for key, value in merged_candidate.items():
            if isinstance(Lesson._meta.get_field(key),ManyToManyField):
                # M2M поля 
                value = sorted(value) if value else []
                orig_val = sorted(list(getattr(original,key).values_list('id', flat=True)))
            else:
                orig_val = getattr(original, f"{key}_id", getattr(original, key, None))

            if value != orig_val:
                # Если обновленнре поле НЕ совпадает с оригиналом - запоминаем
                final_diff[key] = value

        # if str(lesson_id) == "3021": print(LessonReadSerializer(original).data)
        # if str(lesson_id) == "3021": print(final_diff)
        if not final_diff:
            # Если все обновленные поля совпадают с оригинальными значениями - удаляем запись из хранилища
            self.storage.clear_updated(obj_id=lesson_id)
        else:
            self.storage.update_object(obj_id=lesson_id,diff=final_diff)
        self.context = None

    def delete_lessons_draft(self, lesson_id=None):
        self._check_lesson_scenario(lesson_id=lesson_id)
        if lesson_id is not None:
            self.storage.delete_object(obj_id=lesson_id)
        self.context = None

    def apply_lessons(self, lesson_id = None):
        if lesson_id is None:
            self._check_lesson_scenario(lesson_id=lesson_id)
            commit_scenario(self.storage)
        else:
            commit_lesson(self.storage,lesson_id)

    def clear_lessons(self, lesson_id = None):
        if lesson_id is None:
            self.storage.clear_all()
        else:
            self.storage.clear_object(lesson_id)
            return Lesson._default_manager.get(id=lesson_id)
    
    def get_deleted_lessons_draft(self):
        deleted_ids = self.storage.get_deleted() # Получаем список ID из Redis
        return Lesson.objects.filter(id__in=deleted_ids)

    def has_draft(self):
        return self.storage.has_any_changes()
 