import type { Lesson } from "@/types/schedule";
import "@/styles/LessonCard.css";
import { WEEK_DAYS } from "@/types/enums";

interface LessonCardProps {
  lesson: Lesson;
  maxListItems?: number;     // сколько элементов показывать
  limitedHeight?: boolean;   // ограничивать ли высоту
  onShowMoreTeachers?: () => void;
  onShowMoreGroups?: () => void;
}

export const LessonCard = ({
  lesson,
  maxListItems = 1,
  limitedHeight = true,
  onShowMoreTeachers,
  onShowMoreGroups,
}: LessonCardProps) => {
  const showTeachers = lesson.teachers_list || [];
  const showGroups = lesson.groups_list || [];

  const teachersVisible = showTeachers.slice(0, maxListItems);
  const teachersHiddenCount = showTeachers.length - teachersVisible.length;

  const groupsVisible = showGroups.slice(0, maxListItems);
  const groupsHiddenCount = showGroups.length - groupsVisible.length;

  return (
    <div className={`lesson-card flex-col gap-1 ${limitedHeight ? "limited" : ""}`}>
      {/* Заголовок */}
      <div className="lesson-card-title">
        {lesson.type_name} {lesson.discipline_name}
      </div>

      {/* Преподаватели */}
      {teachersVisible.length > 0 && (
        <div className="teacher-list mt-1">
          {teachersVisible.map((t, idx) => (
            <span className="lesson-card-sub" key={idx}>
              👤 {t}
            </span>
          ))}

          {teachersHiddenCount > 0 && (
            <span
              className="lesson-card-sub text-primary"
              style={{ cursor: "pointer", fontWeight: 500 }}
              onClick={onShowMoreTeachers}
            >
              …и ещё {teachersHiddenCount}
            </span>
          )}
        </div>
      )}

      <div className="lesson-divider" />
      {/* Аудитория */}
      <div className="lesson-card-meta">
        Аудитория: {lesson.classroom_name ?? "—"}
      </div>

      {/* Группы */}
      {groupsVisible.length > 0 && (
        <div className="group-list mt-1">
          Группы: {groupsVisible.join(", ")}

          {groupsHiddenCount > 0 && (
            <span
              className="text-primary"
              style={{ cursor: "pointer", fontWeight: 500, marginLeft: 6 }}
              onClick={onShowMoreGroups}
            >
              …и ещё {groupsHiddenCount}
            </span>
          )}
        </div>
      )}
    </div>
  );
};