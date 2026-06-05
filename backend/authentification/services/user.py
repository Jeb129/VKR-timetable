from rest_framework_simplejwt.authentication import JWTAuthentication

from authentification.models import CustomUser
from authentification.serializers import RegisterSerializer

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