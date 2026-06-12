import { DAYS } from "@/types/enums"
import {type Lesson } from "@/types/schedule"
import type { ConstraintError } from "@/types/constraint"
import { useState } from "react"

import "@/styles/constraints.css"

// Вспомогательный компонент для отображения "где и когда" другое занятие
const LessonBrief = ({ lesson }: { lesson: any }) => {
  if (!lesson) return null;
  return (
    <span className="text-muted">
      {`(Занятие #${lesson.id}: ${lesson.discipline}, ${lesson.timeslot.week_num} нед, ${
        DAYS[lesson.timeslot.day-1]?.short_name.toLowerCase() || ""
      }, ${lesson.timeslot.order_number} пара)`}
    </span>
  );
};

const constraintFormatters: Record<
  string,
  (data: any) => React.JSX.Element
> = {
  // --- ЖЕСТКИЕ ---

  teacher_no_overlap: (data) => (
    <ul className="constraint-error-list flex-col gap-1">
      {data.map((v: any, i: number) => (
        <li key={i} className="flex-col">
          <span><strong>{v.teacher.name}</strong> уже ведет занятие:</span>
          <LessonBrief lesson={v.lesson} />
        </li>
      ))}
    </ul>
  ),

  group_no_overlap: (data) => (
    <ul className="constraint-error-list flex-col gap-1">
      {data.map((v: any, i: number) => (
        <li key={i} className="flex-col">
          <span>Группа <strong>{v.group.name}</strong> уже на занятии:</span>
          <LessonBrief lesson={v.lesson} />
        </li>
      ))}
    </ul>
  ),

  room_no_overlap: (data) => (
    <ul className="constraint-error-list flex-col gap-1">
      {data.map((v: any, i: number) => (
        <li key={i} className="flex-col">
          <span>Аудитория <strong>{v.room.name}</strong> занята:</span>
          <LessonBrief lesson={v.lesson} />
        </li>
      ))}
    </ul>
  ),

  room_has_enough_seats: (data) => (
    <div>
      Аудитория <strong>{data.room.name}</strong>: мест {data.capacity}, 
      нужно {data.required}.
    </div>
  ),

  building_travel_impossible_old: (data) => (
    <ul className="constraint-error-list flex-col gap-1">
      {data.map((v: any, i: number) => (
        <li key={i} className="flex-col">
          <span>
            {v.type === 'teacher' ? 'Преподаватель' : 'Группа'} <strong>{v.entity.name}</strong>
          </span>
          <span className="text-danger">
            Путь: {v.travel_time} мин, доступно: {v.available_time} мин.
          </span>
          <LessonBrief lesson={v.neighbor_lesson} />
        </li>
      ))}
    </ul>
  ),
  building_travel_impossible: (data: any[]) => (
    <ul className="constraint-error-list flex-col gap-2 m-0 p-0">
        {data.map((v: any, i: number) => (
            <li key={i} className="constraint-error-item p-2 card flex-col gap-1">
                {/* Заголовок: Кто именно не успевает */}
                <div className="flex-row align-center gap-1">
                    <span className="text-muted small-text">
                        {v.type === 'teacher' ? '👤 Преподаватель:' : '👥 Группа:'}
                    </span>
                    <strong className="text-primary">{v.entity.name}</strong>
                </div>

                {/* Инфо о времени: выделяем красным несоответствие */}
                <div className="flex-row space-between align-center bg-main p-1 rounded-md">
                    <div className="flex-col">
                        <span className="tiny-text uppercase text-muted">В пути</span>
                        <span className="font-bold">{v.travel_time} мин.</span>
                    </div>
                    <div className="text-muted">→</div>
                    <div className="flex-col align-end">
                        <span className="tiny-text uppercase text-muted">Доступно</span>
                        <span className="text-red font-bold">{v.available_time} мин.</span>
                    </div>
                </div>

                {/* Соседнее занятие: чтобы понять, откуда/куда идет человек */}
                <div className="mt-1 pt-1 border-top">
                    <div className="tiny-text uppercase text-muted mb-1">
                        {v.direction === 'prev' ? 'Предыдущая пара:' : 'Следующая пара:'}
                    </div>
                    {/* Используем LessonBrief для краткого отображения дисциплины и кабинета */}
                    <LessonBrief lesson={v.neighbor_lesson} />
                </div>
            </li>
        ))}
    </ul>
),

  // --- ТЕХНИКА / ПРИОРИТЕТ ---

  room_meets_equipment_requirements: (data) => (
    <div className="flex-col">
      <span>Аудитория <strong>{data.room.name}</strong> не имеет:</span>
      <ul className="ml-4">
        {data.missing_equipment.map((e: any, i: number) => (
          <li key={i} className="text-muted">• {e.name}</li>
        ))}
      </ul>
    </div>
  ),

  matches_teacher_room_preference: (data) => (
    <ul className="constraint-error-list flex-col gap-1">
      {data.map((v: any, i: number) => (
        <li key={i}>
          <strong>{v.teacher.name}</strong> предпочитает {v.preferred_room.name}
        </li>
      ))}
    </ul>
  ),

  lessons_ordering: (data) => (
    <ul className="constraint-error-list flex-col gap-1">
      {data.map((v: any, i: number) => (
        <li key={i} className="flex-col">
          <span>Группа <strong>{v.group.name}</strong>: нарушение порядка приоритетов</span>
          <div className="text-muted text-sm">
            Приоритет {v.priorities[0]} перед {v.priorities[1]}
          </div>
        </li>
      ))}
    </ul>
  ),

  matches_teacher_time_preference: (data) => (
    <ul className="constraint-error-list flex-col gap-1">
      {data.map((v: any, i: number) => (
        <li key={i}>
          <strong>{v.teacher.name}</strong> отметил это время как нежелательное
        </li>
      ))}
    </ul>
  ),

  // --- ЭРГОНОМИКА ---

  group_daily_overload: (data) => (
    <ul className="constraint-error-list flex-col gap-1">
      {data.map((v: any, i: number) => (
        <li key={i}>
          Группа <strong>{v.group.name}</strong>: {v.current_hours}ч (лимит {v.limit}ч)
        </li>
      ))}
    </ul>
  ),

  teacher_daily_overload: (data) => (
    <ul className="constraint-error-list flex-col gap-1">
      {data.map((v: any, i: number) => (
        <li key={i}>
          <strong>{v.teacher.name}</strong>: {v.current_hours}ч (лимит {v.limit}ч)
        </li>
      ))}
    </ul>
  ),

  students_gap: (data) => (
    <ul className="constraint-error-list flex-col gap-1">
      {data.map((v: any, i: number) => (
        <li key={i} className="flex-col">
          <span>Окно у группы <strong>{v.group.name}</strong></span>
          <LessonBrief lesson={v.gap_with} />
        </li>
      ))}
    </ul>
  ),

  building_clustering: (data) => (
    <ul className="constraint-error-list flex-col gap-1">
      {data.map((v: any, i: number) => (
        <li key={i}>
          Группа <strong>{v.group.name}</strong> посещает корпуса: {v.buildings.map((b:any) => b.name).join(', ')}
        </li>
      ))}
    </ul>
  ),

  lesson_persistence_sort: (data) => (
    <ul className="constraint-error-list flex-col gap-1">
      {data.map((v: any, i: number) => (
        <li key={i} className="flex-col">
          <span><strong>{v.entity.name}</strong>: короткое занятие между длинными</span>
          <div className="flex-col ml-2 border-l pl-2">
            <LessonBrief lesson={v.longer_before} />
            <LessonBrief lesson={v.longer_after} />
          </div>
        </li>
      ))}
    </ul>
  ),

  morning_preference: (data) => (
    <span>Пара №{data.order}. Желательно ставить занятия в начало дня.</span>
  ),

  teachers_gap: (data) => (
    <ul className="constraint-error-list flex-col gap-1">
      {data.map((v: any, i: number) => (
        <li key={i} className="flex-col">
          <span>Окно у преподавателя <strong>{v.teacher.name}</strong></span>
          <LessonBrief lesson={v.gap_with} />
        </li>
      ))}
    </ul>
  ),

  teacher_weekly_overload: (data) => (
    <ul className="constraint-error-list flex-col gap-1">
      {data.map((v: any, i: number) => (
        <li key={i}>
          <strong>{v.teacher.name}</strong>: {v.hours}ч/нед (лимит {v.limit}ч)
        </li>
      ))}
    </ul>
  ),

  group_weekly_overload: (data) => (
    <ul className="constraint-error-list flex-col gap-1">
      {data.map((v: any, i: number) => (
        <li key={i}>
          Группа <strong>{v.group.name}</strong>: {v.hours}ч/нед (лимит {v.limit}ч)
        </li>
      ))}
    </ul>
  ),
};

interface ConstraintErrorProps {
  error: ConstraintError
}

export const ConstraintErrorItem = ({ error }: ConstraintErrorProps) => {
  // В вашем Python коде вес жестких ограничений — 500
  const isHard = error.penalty >= 500;
  const formatter = constraintFormatters[error.name];

  return (
    <div className={`constraint-error flex-col gap-1 p-2 ${isHard ? "hard" : "soft"}`}>
      <div className="constraint-error-title">
        {error.message}
      </div>
      <div className="constraint-error-content">
        {formatter ? formatter(error.data) : <pre>{JSON.stringify(error.data, null, 2)}</pre>}
      </div>
    </div>
  );
};


interface LessonErrorProps {
    lesson: Lesson
    errors?: ConstraintError[]
}
const LessonErrorItem = ({ lesson, errors }: LessonErrorProps) => {
  const [showDetails, setShowDetails] = useState<boolean>(false);

  return (
    <div className="card lesson-error-card flex-col gap-2 m-1">
      {/* Заголовок */}
      <div className="flex-col gap-1">
        <h4>
          {`(${lesson.id}) ${lesson.lesson_type} ${lesson.discipline}`}
        </h4>

        <span className="text-muted">
          {`Неделя ${lesson.timeslot.week_num}, ${
            DAYS[lesson.timeslot.day-1].short_name.toLowerCase()
          }, ${lesson.timeslot.order_number} пара`}
        </span>
      </div>

      {/* Кнопка */}
      <button
        className="btn btn-outline"
        onClick={() => setShowDetails((prev) => !prev)}
      >
        {showDetails ? "Скрыть детали" : "Показать детали"}
      </button>

      {/* Ошибки */}
      {showDetails && (
        <div className="flex-col gap-2">
          {errors?.map((val, i) => (
            <ConstraintErrorItem key={i} error={val} />
          ))}
        </div>
      )}
    </div>
  );
};
export default LessonErrorItem