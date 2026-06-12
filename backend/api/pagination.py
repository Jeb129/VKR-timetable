from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response

class StandartPagination(PageNumberPagination):
    # Сколько объектов возвращать по умолчанию
    page_size = 10
    
    # Позволяет фронтенду самому указывать размер страницы через ?page_size=20
    page_size_query_param = 'page_size'
    
    # Максимальный лимит, который может запросить фронтенд
    max_page_size = 100
    
    # (Опционально) Переопределяем формат ответа, чтобы он был чище
    def get_paginated_response(self, data):
        return Response({
            'count': self.page.paginator.count, # Общее кол-во объектов
            'results': data                     # Сами данные
        })