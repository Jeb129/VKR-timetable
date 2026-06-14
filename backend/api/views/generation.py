from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from api.models import ScheduleScenario, enums
from api.serializers import StartGenerationSerializer
from api.services.schedule.task_manager import GenerationTaskManager
from authentification.permissions import IsScheduleModerator


class GenerationViewSet(viewsets.ViewSet):

    permission_classes = [IsScheduleModerator]

    def get_scenario(self, scenario_id):
        try:
            return ScheduleScenario.objects.get(id=scenario_id)
        except ScheduleScenario.DoesNotExist:
            return None

    @action(detail=False, methods=["post"])
    def start(self, request, scenario_id=None):
        scenario = self.get_scenario(scenario_id)
        if not scenario:
            return Response(
                {"error": "Сценарий не найден"}, status=status.HTTP_404_NOT_FOUND
            )

        # 1. Валидация входных настроек
        serializer = StartGenerationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        # 2. Запуск задачи через менеджер
        try:
            task_id = GenerationTaskManager.start_task(
                scenario_id=scenario.id,
                semester_id=scenario.semester_id,
                user_id=request.user.id,
                constraints_data=data.get("constraints", []),
                solver_params={
                    "time_limit": data["time_limit"],
                    "num_workers": data["num_workers"],
                },
            )
            return Response(
                {
                    "status": enums.GenerationStatus.IN_PROGRESS,
                    "message": "Процесс генерации запущен успешно",
                },
                status=status.HTTP_202_ACCEPTED,
            )

        except (ValueError, RuntimeError) as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=["post"])
    def stop(self, request, scenario_id=None):
        success = GenerationTaskManager.stop_task(scenario_id)
        if success:
            return Response(
                {
                    "status": enums.GenerationStatus.SUCESS,
                    "message": "Подан сигнал на остановку",
                }
            )
        return Response(
            {"error": "Задача не запущена или уже завершена"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    @action(detail=False, methods=["get"])
    def status(self, request, scenario_id=None):
        info = GenerationTaskManager.get_status(scenario_id)
        # Дополнительно подтянем текущий статус сценария из БД
        scenario = self.get_scenario(scenario_id)
        if scenario:
            info["scenario_status"] = scenario.status

        return Response(info)
