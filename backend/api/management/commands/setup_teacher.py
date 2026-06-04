from django.core.management.base import BaseCommand
from authentification.models import CustomUser
from api.models import Teacher, Lesson, ScheduleScenario, Institute
from django.contrib.auth.hashers import make_password

class Command(BaseCommand):
    help = 'Создание тестового аккаунта преподавателя'

    def handle(self, *args, **options):
        email = "teacher@ksu.ru" # Почта для входа
        password = "password123"

        # 1. Создаем или обновляем пользователя
        user, created = CustomUser.objects.get_or_create(
            email=email,
            defaults={
                'username': 'Teacher_Barilo',
                'password': make_password(password),
                'internal_user': True,
                'is_staff': False # Он не админ!
            }
        )
        if not created:
            user.password = make_password(password)
            user.save()

        # 2. Находим или создаем профиль преподавателя
        inst = Institute.objects.first()
        teacher, _ = Teacher.objects.update_or_create(
            name="Барило И. И.",
            defaults={
                'user': user,
                'institute': inst,
                'constraint_weight': 1
            }
        )

        # 3. Привязываем к нему уроки из EIOS Import
        scenario = ScheduleScenario.objects.filter(is_active=True).first()
        if scenario:
            # Берем уроки по названию дисциплины (как в твоем импорте)
            lessons = Lesson.objects.filter(
                scenario=scenario, 
                discipline__name__icontains="Разработка мультимедийных"
            )
            for lesson in lessons:
                lesson.teachers.add(teacher)
            
            self.stdout.write(self.style.SUCCESS(
                f"Создан пользователь: {email} / {password}\n"
                f"Связан с преподавателем: {teacher.name}\n"
                f"Добавлено пар: {lessons.count()}"
            ))
        else:
            self.stdout.write(self.style.WARNING("Активный сценарий не найден!"))