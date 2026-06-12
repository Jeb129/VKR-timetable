from django.conf import settings
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView, TokenVerifyView
from rest_framework import status
from authentification.serializers import CustomUserSerializer
from authentification.services.user import delete_cookie_tokens, get_cookie_tokens, register_user, set_cookie_tokens

class CookieTokenObtainPairView(TokenObtainPairView):
    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)

        if response.status_code == status.HTTP_200_OK:
            set_cookie_tokens(response)
            response.data["detail"] ="Вход выполнен"
            
        return response

class CookieTokenRefreshView(TokenRefreshView):
    def post(self, request, *args, **kwargs):
        _,refresh_token = get_cookie_tokens(request)
        if not refresh_token:
            return Response(
                {"detail": "Токен обновления сессии не передан"}, 
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        request.data['refresh'] = refresh_token

        response = super().post(request, *args, **kwargs)
        
        if response.status_code == status.HTTP_200_OK:
            set_cookie_tokens(response)
            response.data["detail"] ="Вход выполнен"
        
        return response

class CookieTokenVerifyView(TokenVerifyView):
    def post(self, request, *args, **kwargs):
        token = request.COOKIES.get('access_token')
        if token:
            request.data['token'] = token
        
        return super().post(request, *args, **kwargs)

class LogoutView(APIView):
    def post(self, request):
        try:
            _,refresh_token = get_cookie_tokens(request)
            if refresh_token:
                token = RefreshToken(refresh_token)
                token.blacklist()
            
            res_status = status.HTTP_200_OK
            message = "Выход выполнен"
        except Exception:
            res_status = status.HTTP_401_UNAUTHORIZED
            message = "Невалидный токен, но куки очищены"

        response = Response({"detail": message}, status=res_status)
        delete_cookie_tokens(response)

        return response

class RegisterView(APIView):
    def post(self, request):
        user = register_user(request.data)

        # формируем токены
        refresh = RefreshToken.for_user(user)

        response = Response(CustomUserSerializer(user).data, status=status.HTTP_201_CREATED)
        response["access"] = refresh.access_token
        response["refresh"] = refresh

        set_cookie_tokens(response)
        
        return response