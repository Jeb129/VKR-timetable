from django.core.management.base import BaseCommand
from api.models.requests import BookingType 

class Command(BaseCommand):
    help = 'Наполнение базы данными о типах мероприятий для бронирования'

    def handle(self, *args, **options):
        # Список из вашего ТЗ
        booking_types = [
            "Экскурсия", "День открытых дверей", "Лекция", "Мастер-класс", 
            "Конференция", "Круглый стол", "Форум", "Сессия", "Олимпиада", 
            "Турнир", "Хакатон", "Торжественное мероприятие", "Выпускной/ ПЗ", 
            "Встреча с работодателями", "Буткемп", "Съемка", "Доп образование", 
            "Партнеры", "Развлекательное", "Международное сотрудничество", 
            "Фестиваль/общественное мероприятие", "Интенсив"
        ]

        self.stdout.write(self.style.MIGRATE_LABEL("Начинаю наполнение типов мероприятий..."))

        created_count = 0
        for type_name in booking_types:
            # Ищем по имени, если нет — создаем
            obj, created = BookingType.objects.get_or_create(name=type_name)
            if created:
                created_count += 1
                self.stdout.write(self.style.SUCCESS(f"  + Добавлено: {type_name}"))
            else:
                self.stdout.write(self.style.WARNING(f"  - Уже существует: {type_name}"))

        self.stdout.write(self.style.SUCCESS(
            f"\nГотово! Добавлено новых типов: {created_count}."
        ))