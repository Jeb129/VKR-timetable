from django.db.models import ManyToManyField
from rest_framework import serializers
from django.core.exceptions import ObjectDoesNotExist


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

def get_cached_M2M(model_obj,field:str):
        """Получение M2M связей для занятия без вызова менеджера (без необходимости)"""
        # Сначала проверяем кэш
        cache = getattr(model_obj, '_prefetched_objects_cache', {})
        if field in cache:
            return cache[field]
        
        # Если объекта нет в кэше и нет ID (новый объект), возвращаем пустой список
        if not model_obj.pk:
            return []
            
        # Если ID есть, но кэша нет — обычный запрос
        return getattr(model_obj,field).all()

class SimpleRelatedSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    name = serializers.SerializerMethodField()
    
    def get_name(self, obj):
        return str(obj.name) if hasattr(obj,"name") else str(obj)


class IdNameField(serializers.Field):
    def __init__(self, queryset=None, choices=None, **kwargs):
        self.queryset = queryset
        self.choices = dict(choices) if choices else None
        super().__init__(**kwargs)

    def to_representation(self, value):
        # 1. Если это вариант из choices
        if self.choices is not None:
            return {
                "id": value,
                "name": self.choices.get(value, str(value))
            }

        # 2. Если это объект модели
        if value is None:
            return None
            
        # Проверяем наличие атрибута name, иначе берем str()
        name = getattr(value, 'name', None)
        if name is None:
            name = str(value)

        return {
            "id": value.pk,
            "name": name
        }

    def to_internal_value(self, data):
        # Поле ожидает ID при записи
        if data is None:
            return None

        # 1. Валидация для choices
        if self.choices is not None:
            # Приводим к типу ключей в choices (например, к int)
            # Берем тип первого ключа для приведения
            first_key = next(iter(self.choices.keys()))
            try:
                typed_data = type(first_key)(data)
            except (ValueError, TypeError):
                typed_data = data

            if typed_data not in self.choices:
                raise serializers.ValidationError(f"Выберите корректный вариант. '{data}' нет среди допустимых значений.")
            return typed_data

        # 2. Валидация для queryset
        if self.queryset is not None:
            try:
                return self.queryset.get(pk=data)
            except (ObjectDoesNotExist, TypeError, ValueError):
                raise serializers.ValidationError(f"Объект с id={data} не существует.")

        return data