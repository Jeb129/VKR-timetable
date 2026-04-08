from django.db.models import ManyToManyField


def normalize_diff(model, diff):
    fixed = {}
    for key, value in diff.items():
        field = model._meta.get_field(key)

        # Если поле M2M → всегда список
        if isinstance(field, ManyToManyField):
            # Значение может быть QueryDict-списком или скаляром — приводим к списку
            if isinstance(value, list):
                fixed[key] = value
            else:
                fixed[key] = [value]
            continue

        # Для обычных полей → берём одно значение
        if isinstance(value, list) and len(value) == 1:
            fixed[key] = value[0]
        else:
            fixed[key] = value

    return fixed
