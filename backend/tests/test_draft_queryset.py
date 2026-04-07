from datetime import date
from os import name

import pytest
from django.contrib.auth.models import User
from django.db import transaction

from api.models import *
from api.services.redis.storage import RedisDraftStorage
from api.services.schedule.draft.context import draft_context

def init_scenario():
    semester, _ = Semester.objects.get_or_create(
        name="Тестовый семестр 2026",
        date_start= date(2026, 2, 1),
        date_end= date(2026, 7, 31),
    )
    scenario, _ =  ScheduleScenario.objects.get_or_create(
        name="Test Scenario",
        semester=semester,
        is_active=True,
        )
    return scenario

def init_group():
    inst, _ = Institute.objects.get_or_create(
        name = "Институт"
    )
    programm, _ = StudyProgram.objects.get_or_create(
        institute = inst,
        name = "Программа",
        short_name = "Прог"
    )
    return StudyGroup.objects.create(
        admission_year = 22,
        stud_program = programm,
        learning_form = "o",
        learning_stage = "b",
        group_num=1,
        name="Группа",
        students_count=20
    )

def init_lesson(scenario):
    t1, _ = Timeslot.objects.get_or_create(day=1,week_num=1,order_number=1,time_start="08:30", time_end="10:00")
    c1, _ = Classroom.objects.get_or_create(num="101",name="аудитория",capacity=30)

    return Lesson.objects.create(
        scenario=scenario,
        timeslot=t1,
        classroom=c1,
        discipline=Discipline.objects.create(name="Дисциплина"),
        lesson_type=LessonType.objects.create(name="занятие")
    )

@pytest.mark.django_db
def test_updated_lesson_fields_are_overridden(redis_client):
    """
    Проверяем, что updated diff подмешивается к Lesson.
    """
    scenario = init_scenario()
    lesson = init_lesson(scenario)

    storage = RedisDraftStorage(scenario.id, user_id=1,redis=redis_client)
    storage.update_lesson(lesson.id, {"timeslot": None})
    with draft_context(scenario, storage) as manager:
        draft = Lesson.objects.get(id=lesson.id)
        assert draft.timeslot is None


@pytest.mark.django_db
def test_deleted_lesson_not_visible(redis_client):
    """
    Удалённый урок не должен попадать в выборку.
    """
    scenario = init_scenario()
    lesson = init_lesson(scenario)

    storage = RedisDraftStorage(scenario.id, user_id=1,redis=redis_client)
    storage.delete_lesson(lesson.id)

    with draft_context(scenario, storage):
        lessons = list(Lesson.objects.all())
        assert lesson.id not in [l.id for l in lessons]


@pytest.mark.django_db
def test_created_lessons_are_returned(redis_client):
    """
    Проверяем, что lessons из `created` появляются в выборке.
    """
    scenario = ScheduleScenario.objects.create(name="Test Scenario")

    storage = RedisDraftStorage(scenario.id, user_id=1,redis=redis_client)
    t1, _ = Timeslot.objects.get_or_create(day=1,week_num=1,order_number=1,time_start="08:30", time_end="10:00")
    c1, _ = Classroom.objects.get_or_create(num="101",name="аудитория",capacity=30)
    storage.create_lesson({
        "timeslot": 1,
        "classroom": 1,
        "discipline": 1,
        "lesson_type": 1,
    })

    with draft_context(scenario, storage):
        lessons = list(Lesson.objects.all())
        # Один новый урок + (0 реальных)
        assert len(lessons) == 1
        assert lessons[0].id is None


@pytest.mark.django_db
def test_manager_restored_after_context(redis_client):
    """
    Менеджеры Lesson.objects должны быть восстановлены после выхода из контекста.
    """
    scenario = init_scenario()

    storage = RedisDraftStorage(scenario.id, user_id=1,redis=redis_client)

    original_manager = Lesson.objects.__class__

    with draft_context(scenario, storage):
        inside_manager = Lesson.objects.__class__
        assert inside_manager is not original_manager

    after_manager = Lesson.objects.__class__
    assert after_manager is original_manager


@pytest.mark.django_db
def test_m2m_override(redis_client):
    """
    Проверяем, что M2M подменяется корректно: _draft_teachers.
    """
    scenario = init_scenario()
    lesson = init_lesson(scenario)
    group1 = init_group()
    group2 = init_group()

    lesson.study_groups.add(group1)

    storage = RedisDraftStorage(scenario.id, user_id=1,redis=redis_client)
    storage.update_lesson(lesson.id, {"groups": [group1.id, group2.id]})

    with draft_context(scenario, storage):
        draft = Lesson.objects.get(id=lesson.id)
        assert draft.study_groups.values_list("id",flat=True) == [group1.id, group2.id]
        # Проверяем, что реальные связи не менялись
        assert list(lesson.study_groups.all()) == [group1]


@pytest.mark.django_db
def test_outside_context_no_changes(redis_client):
    """
    Вне draft_context должен работать обычный ORM.
    """
    scenario = init_scenario()
    lesson = init_lesson(scenario)

    storage = RedisDraftStorage(scenario.id, user_id=1,redis=redis_client)
    storage.update_lesson(lesson.id, {"timeslot": 123})  # такого timeslot нет

    # ВНЕ контекста — никаких изменений
    fresh = Lesson.objects.get(id=lesson.id)
    assert fresh.timeslot_id != 123