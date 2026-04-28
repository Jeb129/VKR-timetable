from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from django.utils import timezone
from django.http import HttpResponse
import logging
import json


from io import BytesIO

from api.serializers import ExcelUploadSerializer, ValidationMeassageSerializer
from api.services.data_import.excel import import_excel
from api.services.data_import.loaders import AcademicLoadReader, export_loading

# твои функции
# from .excel import import_excel, export_excel
logger = logging.getLogger("Load")

class ExcelAPIView(APIView):
    """
    POST  -> загрузка Excel
    GET   -> выгрузка Excel
    """

    permission_classes = [IsAuthenticated]

    def post(self, request):
            serializer = ExcelUploadSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            
            file = serializer.validated_data["file"]
            # читаем Excel напрямую из upload
            data = import_excel(file)
            load_stream = AcademicLoadReader(data)
            messages = list(load_stream)

            return Response(
                {
                    "rows": len(data),
                    "success": load_stream.success_counter,
                    "skipped": load_stream.skipped_counter,
                    "errors": load_stream.error_counter,
                    "messages": ValidationMeassageSerializer(messages, many=True).data,
                    "created": {
                        "study_programs": load_stream.programs_created_counter,
                        "disciplines": load_stream.discipline_created_counter,
                        "groups": load_stream.groups_created_counter,
                        "teachers": load_stream.teachers_created_counter,
                    },
                    "exists": {
                        "study_programs": load_stream.programs_exists_counter,
                        "disciplines": load_stream.discipline_exists_counter,
                        "groups": load_stream.groups_exists_counter,
                        "teachers": load_stream.teachers_exists_counter,
                    },
                },
                status=status.HTTP_200_OK,
            )

    def get(self, request):
        try:
            # пример данных (замени на свои сервисы/БД)
            now = timezone.localtime(timezone.now())
            filename = f"Нагрузка_{now.strftime("%Y-%m-%d_%H-%M-%S")}.xlsx"
            buffer = BytesIO()
            # экспорт в поток
            export_loading(buffer)
            buffer.seek(0)
            response = HttpResponse(
                buffer.read(),
                content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )
            response["Content-Disposition"] = f'attachment; filename="{filename}"'
            response["Access-Control-Expose-Headers"] = "Content-Disposition"
            return response
        except Exception as e:
            logger.error(f"Ошибка при экспорте Excel: {str(e)}")
            return Response(
                {"error": "Не удалось сформировать файл экспорта"}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
