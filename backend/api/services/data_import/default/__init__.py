from .constraints import init_building_priorities, init_constraints, init_travel_times
from .institutes import init_buildings, init_institutes

from .meta import init_lesson_types, init_semesters, init_timeslots


def init_default():
    return (
        init_timeslots(),
        init_semesters(),
        init_lesson_types(),
        init_institutes(),
        init_buildings(),
        init_building_priorities(),
        init_travel_times(),
        init_constraints()
    )