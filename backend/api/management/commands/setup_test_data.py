from django.core.management.base import BaseCommand
from authentification.models import CustomUser
from api.models import Teacher, Lesson, ScheduleScenario

class Command(BaseCommand):
    help = 'Точная привязка преподавателя Барило И.И. к его реальным парам'

    def handle(self, *args, **options):
        user = CustomUser.objects.filter(email="aidyakov05@gmail.com").first()
        if not user:
            self.stdout.write(self.style.ERROR("Пользователь не найден!"))
            return

        # 1. Находим преподавателя
        teacher = Teacher.objects.filter(name__icontains="Барило").first()
        if not teacher:
            self.stdout.write(self.style.ERROR("Преподаватель Барило не найден в БД!"))
            return

        # 2. Связываем его с твоим пользователем
        teacher.user = user
        teacher.save()
        
        user.internal_user = True
        user.save()

        # 3. Находим все уроки в активном сценарии, где в названии (или через импорт) должен быть Барило
        # В идеале, если при импорте из JSON мы не заполнили поле teachers, нам нужно это исправить
        scenario = ScheduleScenario.objects.filter(is_active=True).first()
        
        # Очистим старые привязки этого учителя для чистоты теста
        teacher.lesson_set.clear()

        # Если в Lesson нет информации о том, чей это урок, привяжем его к урокам конкретных дисциплин, 
        # которые он ведет (например, "Разработка мультимедийных приложений")
        relevant_lessons = Lesson.objects.filter(
            scenario=scenario, 
            discipline__name__icontains="Разработка мультимедийных"
        )

        for lesson in relevant_lessons:
            lesson.teachers.add(teacher)

        self.stdout.write(self.style.SUCCESS(
            f"Успех! Преподаватель {teacher.name} связан с {user.email}. "
            f"Ему назначено {relevant_lessons.count()} тематических уроков."
        ))