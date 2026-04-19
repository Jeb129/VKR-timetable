import { WEEK_DAYS } from "@/types/enums"
import {type Lesson } from "@/types/schedule"
import type { ConstraintError } from "@/types/constraint"
import { useState } from "react"

import "@/styles/constraints.css"

const constraintFormatters: Record<
  string,
  (data: any) => React.JSX.Element
> = {
  teacher_no_overlap: (data) => {
    const list = Array.isArray(data) ? data : [];

    return (
      <ul className="constraint-error-list flex-col gap-1">
        {list.map((entry: any, idx: number) => {
          const teacherNames = entry.teachers
            .map((t: any) => t.name)
            .join(", ");

          return (
            <li key={idx} className="constraint-error-item flex-col gap-1">
              <span>
                <strong>{teacherNames}</strong>
                {" — занят(ы) в занятии №"}
                {entry.lesson.id}
              </span>

              <span className="text-muted">
                {`Неделя ${entry.lesson.week_num}, ${
                  WEEK_DAYS[entry.lesson.day][0].toLowerCase()
                }, ${entry.lesson.order} пара`}
              </span>
            </li>
          );
        })}
      </ul>
    );
  },
  group_no_overlap: (data) => {
    const list = Array.isArray(data) ? data : [];

    return (
      <ul className="constraint-error-list flex-col gap-1">
        {list.map((entry: any, idx: number) => {
          const groupNames = entry.groups
            .map((t: any) => t.name)
            .join(", ");

          return (
            <li key={idx} className="constraint-error-item flex-col gap-1">
              <span>
                <strong>{groupNames}</strong>
                {" — занят(ы) в занятии №"}
                {entry.lesson.id}
              </span>

              <span className="text-muted">
                {`Неделя ${entry.lesson.week_num}, ${
                  WEEK_DAYS[entry.lesson.day][0].toLowerCase()
                }, ${entry.lesson.order} пара`}
              </span>
            </li>
          );
        })}
      </ul>
    );
  },
};

interface ConstraintErrorProps {
    error: ConstraintError
}
export const ConstraintErrorItem = ({ error }: ConstraintErrorProps) => {
  const isHard = error.penalty === 500;
  const formatter = constraintFormatters[error.name];

  return (
    <div
      className={`constraint-error flex-col gap-1 p-2 ${
        isHard ? "" : "soft"
      }`}
    >
      <div className="constraint-error-title">
        {error.message}
      </div>

      {formatter?.(error.data)}
    </div>
  );
};

interface LessonErrorProps {
    lesson: Lesson
    errors: ConstraintError[]
}
const LessonErrorItem = ({ lesson, errors }: LessonErrorProps) => {
  const [showDetails, setShowDetails] = useState<boolean>(false);

  return (
    <div className="card lesson-error-card flex-col gap-2 m-1">
      {/* Заголовок */}
      <div className="flex-col gap-1">
        <h4>
          {`(${lesson.id}) ${lesson.type_name} ${lesson.discipline_name}`}
        </h4>

        <span className="text-muted">
          {`Неделя ${lesson.week_num}, ${
            WEEK_DAYS[lesson.day][0].toLowerCase()
          }, ${lesson.order} пара`}
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
          {errors.map((val, i) => (
            <ConstraintErrorItem key={i} error={val} />
          ))}
        </div>
      )}
    </div>
  );
};
export default LessonErrorItem