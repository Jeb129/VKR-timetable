import logging
from typing import Dict, List, Optional

from django.db.models import ManyToManyField

from api.models import Constraint, Lesson
from api.services.constraunt.constraints import registry
from api.services.constraunt.context import ScheduleContext
from api.services.constraunt.meta import ConstraintError, LessonError
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
        
        # Данные загружаются при создании экземпляра
        self.constraints: List[Constraint] = []
        self.methods: Dict[str, callable] = {}
        self._load_constraints()

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
    
    def _load_constraints(self):
        """Загружает ограничения и сопоставляет с реализованными функциями."""
        logger.info("Проверка реализации ограничений")

        for c in Constraint.objects.all():
            func = registry.get(c.name)
            if func:
                self.constraints.append(c)
                self.methods[c.name] = func
                logger.debug("Успешная инициализация ограничения %s", c.name)
            else:
                logger.warning("Метод проверки ограничения '%s' не найден.",c.name)

        return self

    def build_context(self,*,draft = False):
        if draft:
            with draft_context(self.scenario_id, self.storage):
                self.context = ScheduleContext(self.scenario_id)
        else:
            self.context = ScheduleContext(self.scenario_id)
        return self
    
    
    def check_lesson(self, lesson, constraint_name = None):
        """Проверяет занятие в сценарии по всем ограничениям"""
        if self.context is None:
            self.build_context()

        errors = []
        constraints = (
            [c for c in self.constraints if c.name == constraint_name] 
            if constraint_name else self.constraints
        )
        for c in constraints:
            func = self.methods.get(c.name)
            if func is None:
                continue
            try:
                logger.debug("Проверка ограничения %s", c.name)
                res = func(lesson, self.context, weight=c.weight)
                if not (res is None or c.generation_only):
                    errors.append(res)
            except Exception as err:
                logger.error("Ошибка при проверке ограничения %s для занятия %s", c.name, lesson.id)
                errors.append(ConstraintError(
                    name=c.name,
                    message="Ошибка при проверке",
                    data=err
                ))
        return LessonError(lesson,errors)

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
        return self.storage.create_object(data=data)

    def get_lessons_draft(self,*args,**kwargs):
        """Поиск в контексте"""
        if self.context is None:
            raise ValueError("Не собран контекст поиска. Вызовите ScheduleManager.build_context() перед вызовом метода get_lessons_draft")
        return self.context.filter(*args,**kwargs)
    
    def update_lesson_draft(self,lesson_id, diff_data):
        """Вносит изменения в черновик расписания"""
        if str(lesson_id) in self.storage.get_created():
            # если занятие - созданный черновик, то пересоздаем
            self.storage.create_object(data=diff_data,nes_id=str(lesson_id))
            # Пересобираем контекст с обновленным занятием и проверяем
            return self.check_lesson_draft(lesson_id, build_context=True)
        
        # Получаем оригинальное занятие
        original = Lesson._default_manager.prefetch_related('teachers', 'study_groups').get(id=lesson_id)
        self._check_lesson_scenario(lesson=original)
        
        # Собираем все хранящиеся и входящие изменения в один список
        merged_candidate = {
            **self.storage.get_updated().get(lesson_id, {}), 
            **diff_data}

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

        if not final_diff:
            # Если все обновленные поля совпадают с оригинальными значениями - удаляем запись из хранилища
            self.storage.clear_updated(obj_id=lesson_id)
        else:
            self.storage.update_object(obj_id=lesson_id,diff=final_diff)

        # Пересобираем контекст с обновленным занятием и проверяем
        return self.check_lesson_draft(lesson_id, build_context=True)

    def delete_lessons_draft(self, lesson_id=None):
        self._check_lesson_scenario(lesson_id=lesson_id)
        if lesson_id is not None:
            self.storage.delete_object(obj_id=lesson_id)
        else:
            self.storage.clear_all()
    
    def apply_lessons(self, lesson_id=None):
        if lesson_id is None:
            self._check_lesson_scenario(lesson_id=lesson_id)
            commit_scenario(self.storage)
        else:
            commit_lesson(self.storage,lesson_id)
        

    def has_draft(self):
        return self.storage.has_any_changes()
 