from authentification.models import CustomUser
from authentification.serializers import RegisterSerializer

def register_user(data) -> CustomUser:
    serializer = RegisterSerializer(data=data)
    serializer.is_valid(raise_exception=True)

    return serializer.save()