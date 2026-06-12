from rest_framework_simplejwt.authentication import JWTAuthentication
from django.conf import settings
from rest_framework.response import Response
from rest_framework.request import Request
from authentification.models import CustomUser
from authentification.serializers import RegisterSerializer

def get_cookie_tokens(request:Request):
    access = request.COOKIES.get('access_token')
    refresh = request.COOKIES.get('refresh_token')
    return access,refresh
    

def set_cookie_tokens(response:Response):
    access = response.data.get('access')
    if access is not None:
        response.set_cookie(
            key='access_token',
            value=access,
            httponly=True,
            secure=not settings.DEBUG,  # В проде True (HTTPS)
            samesite='Lax',
            max_age=settings.SIMPLE_JWT['ACCESS_TOKEN_LIFETIME'].total_seconds()
        )
        del response.data['access']

    refresh = response.data.get('refresh')
    if refresh is not None:
        response.set_cookie(
            key='refresh_token',
            value=refresh,
            httponly=True,
            secure=not settings.DEBUG,
            samesite='Lax',
            max_age=settings.SIMPLE_JWT['REFRESH_TOKEN_LIFETIME'].total_seconds()
        )
        del response.data['refresh']
    
    return response

def delete_cookie_tokens(response:Response):
    response.delete_cookie('access_token')
    response.delete_cookie('refresh_token')
    
    return response

def register_user(data) -> CustomUser:
    serializer = RegisterSerializer(data=data)
    serializer.is_valid(raise_exception=True)

    return serializer.save()


class CustomJWTAuthentication(JWTAuthentication):
    def authenticate(self, request):
        # Пытаемся достать токен из кук
        raw_token = request.COOKIES.get('access_token')
        
        if raw_token is None:
            return None

        validated_token = self.get_validated_token(raw_token)
        return self.get_user(validated_token), validated_token