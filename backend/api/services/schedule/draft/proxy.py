class DraftRelationProxy:
    """
    Proxy для M2M поля в черновиках.
    Поддерживает фильтры по id и Python iteration.
    """
    def __init__(self, model, ids):
        self.model = model
        self._ids = set(ids)
    
    def all(self):
        return self.model.objects.filter(id__in=self._ids)

    def __iter__(self):
        return iter(self.all())

    def values_list(self, *args, **kwargs):
        return self.all().values_list(*args, **kwargs)

    def add(self, *objs):
        for o in objs:
            self._ids.add(o.id)

    def remove(self, *objs):
        for o in objs:
            self._ids.discard(o.id)

    def __contains__(self, item):
        return getattr(item, "id", item) in self._ids