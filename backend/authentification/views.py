import requests
from rest_framework import status
from django.conf import settings
from rest_framework.generics import RetrieveAPIView
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken

from authentification.serializers import CustomUserSerializer
from authentification.services.user import register_user

# Имитация API Moodle (Mock)
class MockMoodleAPIView(APIView):
    permission_classes = [AllowAny]
    def get(self, request):
        email = request.query_params.get("criteria[0][value]")
        # Имитируем, что в Moodle всегда есть пользователь с таким email
        return Response({
            "users": [{
                "id": 777,
                "fullname": "Тестовый Студент КГУ",
                "email": email
            }]
        })

#  Логика верификации 
class MoodleVerifyView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user = request.user
        
        # Если токена нет в settings, шлем запрос на наш же Mock
        moodle_url = getattr(settings, "MOODLE_URL", "http://localhost:8000/auth/mock-moodle/")
        moodle_token = getattr(settings, "MOODLE_TOKEN", "fake-token")

        params = {
            "wstoken": moodle_token,
            "wsfunction": "core_user_get_users",
            "moodlewsrestformat": "json",
            "criteria[0][key]": "email",
            "criteria[0][value]": user.email,
        }

        try:
            response = requests.get(moodle_url, params=params, timeout=10)
            data = response.json()

            if "users" in data and len(data["users"]) > 0:
                moodle_user = data["users"][0]
                
                # Привязываем статус "Внутренний пользователь" (internal_user)
                user.internal_user = True
                user.moodle_id = moodle_user["id"]
                user.save()

                return Response({"message": "Аккаунт успешно подтвержден через СДО Moodle!"})
            
            return Response({"error": "Email не найден в базе данных Moodle"}, status=404)
        except Exception as e:
            return Response({"error": f"Ошибка связи с сервером подтверждения"}, status=502)

class RegisterView(APIView):
    def post(self, request):
        user = register_user(request.data)

        # формируем токены
        refresh = RefreshToken.for_user(user)

        return Response({
            "user": {
                "id": user.id,
                "email": user.email,
                "name": user.username,  # или другое поле имени
            },
            "access": str(refresh.access_token),
            "refresh": str(refresh),
        }, status=status.HTTP_201_CREATED)

class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            RefreshToken(request.data.get("refresh")).blacklist()
        except Exception:
            return Response({"detail": "Невалидный токен"}, status=400)
        return Response({"detail": "Выход выполнен, сессия отозвана"})

class CurrentUserView(RetrieveAPIView):
    permission_classes= [IsAuthenticated]
    serializer_class = CustomUserSerializer

    def get_object(self):
        return self.request.user
    
    def destroy(self, request, *args, **kwargs):
        user = self.get_object()
        user.is_active = False
        user.save()
        return Response(status=status.HTTP_204_NO_CONTENT)