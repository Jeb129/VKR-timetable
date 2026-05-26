# На текущий момент реализованы следующие ограничения
# Импорт модулей с методами осуществляется здесь

# в менеджере используется импорт модуля напрямую + импорт списка ограничений:

# import api.services.constraints.methods
# from api.services.constraints.meta import registry


#               Описание                    Вес    Имя метода для проверки
# ---------------------------------------Жёсткие---------------------------------------
# Пересечение по преподавателю	            500    teacher_no_overlap
# Пересечение по группе	                    500    group_no_overlap
# Пересечение по аудиториям	                500	   room_no_overlap
# Аудитория вмещает всех студентов          500	   room_has_enough_seats
# Невозможность перехода между корпусами    500	   building_travel_impossible
#
# ---------------------------------Техника / приоритет---------------------------------
# Аудитория соответствует оборудованию      400	   room_meets_equipment_requirements
# Предпочтения преподавателя по аудитории	300    matches_teacher_room_preference
# Ручной приоритет (упорядочивание)	        300    lessons_ordering
# Предпочтения преподавателя по времени	    200	   matches_teacher_time_preference
#
# --------------------------------Эргономика / качество--------------------------------
# Дневная перегрузка группы	                150	   group_daily_overload
# Дневная перегрузка преподавателя	        100	   teacher_daily_overload
# Окно у студентов	                        100	   students_gap
# Факт смены корпуса в течение дня	        100	   building_clustering
# Позиционирование временных занятий	    100	   lesson_persistence_sort
# Приоритет заполнения первой половины дня	80	   morning_preference
# Окно у преподавателя	                    50	   teachers_gap
# Недельная перегрузка преподавателя	    50	   teacher_weekly_overload
# Недельная перегрузка группы	            50	   group_weekly_overload


from . import hard
from . import priorities
from . import quality
