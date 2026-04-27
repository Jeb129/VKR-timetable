import re
import logging
from dataclasses import dataclass

CODE_REGEX = re.compile(r"^\d+\.\d+\.\d+$")
BOOL_TRUE = {"истина", "true", "1", "да"}
BOOL_FALSE = {"ложь", "false", "0", "нет", ""}


@dataclass
class ValidationMessage:
    idx: int | None
    level: str
    field: str
    message: str

    def __str__(self):
        return f"[{self.level}] Строка {self.idx} | {self.field}: {self.message}"


def is_empty(v):
    return isinstance(v, float) or v is None or str(v).strip() == ""


def parse_bool_or_none(value):
    """Возвращает True/False или None если нельзя интерпретировать."""
    if value is None:
        return False  # по вашим правилам NULL → False

    val = str(value).strip().lower()
    if val in BOOL_TRUE:
        return True
    if val in BOOL_FALSE:
        return False
    return None


def parse_int_or_none(value):
    """Пытается интерпретировать значение как int, иначе возвращает None."""
    try:
        return int(value)
    except:
        return None


def validate_row(row, idx):
    errors = []

    def err(field, message):
        errors.append(ValidationMessage(idx,"WARNING", field, message))

    # Разбор полей (строго 22, как в выгрузке)
    (
        institute,
        code,
        name,
        short_name,
        discipline,
        allow_merge,
        lt_name,
        lt_short,
        semester,
        form_control,
        weeks,
        hours,
        teacher_inst,
        teacher_name,
        teacher_post,
        admission_year,
        group_num,
        subgroup,
        learning_form,
        learning_stage,
        students,
        merge_key,
    ) = row[:22]

    # ----------- Проверка + нормализация -----------

    # Институт направления
    if is_empty(institute):
        err("Направление.Институт", "Обязательное поле")

    # Шифр направления
    code_str = None
    if is_empty(code):
        err("Направление.Шифр", "Обязательное поле")
    else:
        s = str(code).strip()
        if CODE_REGEX.match(s):
            code_str = s
        else:
            err("Направление.Шифр", "Формат должен быть X.X.X")
            code_str = s  # возвращаем как есть, чтобы не терять данные

    # Наименование направления
    if is_empty(name):
        err("Направление.Наименование", "Обязательное поле")

    # Название дисциплины
    if is_empty(discipline):
        err("Дисциплина.Название", "Обязательное поле")

    # allow_merge
    parsed_allow_merge = parse_bool_or_none(allow_merge)
    if parsed_allow_merge is None:
        err(
            "Дисциплина.allow_merge_teachers",
            f"Некорректное логическое значение: {allow_merge}",
        )

    # Вид занятия (OR)
    if is_empty(lt_name) and is_empty(lt_short):
        err("Вид занятия", "Название или сокращение должно быть заполнено")

    # Семестр
    semester_int = None
    if is_empty(semester):
        err("Нагрузка.Семестр", "Обязательное поле")
    else:
        semester_int = parse_int_or_none(semester)
        if semester_int is None or semester_int < 1:
            err("Нагрузка.Семестр", "Должен быть целым числом >= 1")

    # Недели
    weeks_int = parse_int_or_none(weeks)
    if weeks_int is None:
        err("Нагрузка.Недели", "Должно быть целым числом >= 0")
    elif weeks_int < 0:
        err("Нагрузка.Недели", "Должно быть >= 0")

    # Часы
    hours_int = parse_int_or_none(hours)
    if hours_int is None:
        err("Нагрузка.Часы", "Должно быть целым числом >= 0")
    elif hours_int < 0:
        err("Нагрузка.Часы", "Должно быть >= 0")

    # Преподаватель ФИО
    if is_empty(teacher_name):
        err("Преподаватель.ФИО", "Обязательное поле")

    # Год поступления
    admission_year_int = None
    if is_empty(admission_year):
        err("Группа.Год", "Обязательное поле")
    else:
        admission_year_int = parse_int_or_none(admission_year)
        if admission_year_int is None or admission_year_int < 0:
            err("Группа.Год", "Должен быть целым числом >= 0")

    # Номер группы (строка)
    if is_empty(group_num):
        err("Группа.Номер группы", "Обязательное поле")
    group_num_str = None if is_empty(group_num) else str(group_num).strip()

    # Подгруппа
    subgroup_int = None
    if not is_empty(subgroup):
        subgroup_int = parse_int_or_none(subgroup)
        if subgroup_int is None or subgroup_int < 1:
            err("Группа.Подгруппа", "Должна быть целым числом >= 1")

    # Форма обучения
    if is_empty(learning_form):
        err("Группа.Форма обучения", "Обязательное поле")

    # Уровень
    if is_empty(learning_stage):
        err("Группа.Уровень подготовки", "Обязательное поле")

    # Студенты
    students_int = None
    if is_empty(students):
        err("Группа.Количество студентов", "Обязательное поле")
    else:
        students_int = parse_int_or_none(students)
        if students_int is None or students_int < 1:
            err("Группа.Количество студентов", "Должно быть числом >= 1")

    # merge_key — невалидируем, оставляем как есть
    merge_key_val = None if is_empty(merge_key) else str(merge_key)

    # ----------- Формируем нормализованный кортеж -----------

    normalized = (
        institute,
        code_str,
        name,
        short_name,
        discipline,
        parsed_allow_merge,
        lt_name,
        lt_short,
        semester_int,
        form_control,
        weeks_int,
        hours_int,
        teacher_inst,
        teacher_name,
        teacher_post,
        admission_year_int,
        group_num_str,
        subgroup_int,
        learning_form,
        learning_stage,
        students_int,
        merge_key_val,
    )

    return errors, normalized
