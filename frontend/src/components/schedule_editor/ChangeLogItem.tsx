// components/schedule_editor/ChangeLogItem.tsx
import { type Lesson } from "@/types/schedule";
import { DiffItem } from "./DiffItem";
import "@/styles/ChangeLog.css";

const fieldLabels: Record<string, string> = {
    classroom: "Аудитория",
    timeslot: "Время",
    teachers: "Преподаватели",
    study_groups: "Группы",
    discipline: "Дисциплина"
};

export const ChangeLogItem = ({ lesson, onRevert }: { lesson: Lesson, onRevert: (id: string) => void }) => {
    const info = lesson.draft_info;
    if (!info) return null;

    return (
        <div className="change-item card p-2 mb-2 flex-col gap-2">
            <div className="flex-row space-between align-center">
                <div className="flex-row gap-1 align-center">
                    <span className={`badge ${info.is_new ? 'btn-green' : 'btn-primary'} py-0`}>
                        {info.is_new ? 'НОВОЕ' : 'ИЗМЕНЕНО'}
                    </span>
                </div>
                <button className="revert-btn" onClick={() => onRevert(lesson.id)}>↺</button>
            </div>

            <div className="text-primary font-bold">ID:{lesson.id} {lesson.lesson_type} {lesson.discipline}</div>

            <div className="flex-col gap-2 border-top mt-1 pt-1">
                {info.changes.map((change, idx) => (
                    <div key={idx} className="flex-col gap-1">
                        <span className="text-muted tiny-text uppercase font-bold">
                            {fieldLabels[change.field] || change.field}
                        </span>
                        <div className="flex-row align-center gap-1 flex-wrap">
                            <DiffItem value={change.was} className="text-muted line-through small-text" />
                            <span className="text-muted">→</span>
                            <DiffItem value={change.now} className="text-primary small-text" />
                        </div>
                    </div>
                ))}
            </div>
        </div>
    );
};