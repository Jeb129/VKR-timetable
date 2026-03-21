from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken

from authentification.services.user import register_user


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