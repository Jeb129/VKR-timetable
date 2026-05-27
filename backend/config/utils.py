from django.db.models import ManyToManyField
from rest_framework import serializers


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