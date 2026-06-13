from rest_framework import status
from rest_framework.generics import RetrieveAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from rest_framework.views import APIView


from api.models import Teacher
from authentification.permissions import IsEmailVerified
from authentification.serializers import CustomUserSerializer
from authentification.services.moodle import find_student_profile, find_teacher_profile, moodle_get_profiles, moodle_get_user

#  Логика верификации
class MoodleVerifyView(APIView):
    permission_classes = [IsAuthenticated]
    # По идее подтверждение доступно только при подтвержденной почте
    # permission_classes = [IsAuthenticated,IsEmailVerified]


    def post(self, request):
        user = request.user
        try:
            # Находим Moodle ID по Email
            m_user = moodle_get_user(user)
            if not m_user:
                return Response(
                    {"error":"Пользователь с таким Email не найден в Moodle"},
                    status.HTTP_404_NOT_FOUND
                )
            
            m_id,m_fullname = m_user
            user.internal_user = True
            user.moodle_id = m_id

            profiles = moodle_get_profiles(m_id)
            if not profiles:
                return Response(
                    {"message": "Ваш профиль найден в системе Moodle, но вы не зачислены ни на один курс.\nНевозможно определить вашу роль", "is_teacher": False},
                    status=status.HTTP_200_OK
                )

            is_teacher = find_teacher_profile(profiles) is not None
            msg = "Ваш ппрофиль найден в системе Moodle"

            if is_teacher:
                # Ищем преподавателя по ФИО в нашей базе
                teacher_obj = Teacher.objects.filter(name__icontains=m_fullname).first()
                if teacher_obj:
                    user.teacher = teacher_obj
                    msg = f"Вы подтверждены как преподаватель: {m_fullname}"
                else:
                    msg = f"В Moodle вы учитель, но в базе расписания ФИО {m_fullname} не найдено."
            return Response(
                {"message": msg, "is_teacher": is_teacher},
                status=status.HTTP_200_OK
            )

        except Exception as e:
            return Response(
                {"error": f"Ошибка взаимодействии с Moodle: {str(e)}"}, 
                status=status.HTTP_502_BAD_GATEWAY
            )
        
        finally:
            user.save()

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

class UserView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        serializer = CustomUserSerializer(request.user)
        return Response(serializer.data)

class LinkGroupView(APIView):
    permission_classes = [IsAuthenticated]

    def patch(self, request):
        user = request.user
        group_id = request.data.get("study_group_id")

        if not group_id:
            return Response({"error": "ID группы не передан"}, status=400)
            
        # Проверяем, что пользователь действительно прошел Moodle
        if not user.internal_user:
            return Response({"error": "Сначала подтвердите аккаунт через Moodle"}, status=403)

        group = get_object_or_404(StudyGroup, id=group_id)
        
        user.study_group = group
        user.save()
        
        return Response({"message": f"Вы привязаны к группе {group.name}"}, status=200)