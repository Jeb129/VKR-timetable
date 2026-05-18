import { type Lesson } from "@/types/schedule";

interface Props {
    lesson: Lesson;
    onRestore: (id: string) => void;
}

export const DeletedLogItem = ({ lesson, onRestore }: Props) => (
    <div className="error-item fade-in" style={{ borderColor: 'var(--p-red)', background: 'var(--white)' }}>
        <div className="flex-row space-between align-center">
            <div className="flex-col">
                <div className="error-title" style={{ color: 'var(--p-red)' }}>{lesson.discipline}</div>
                <div className="text-muted" style={{ fontSize: '12px' }}>
                    Было: {lesson.classroom} | {lesson.timeslot.time_start.substring(0, 5)}
                </div>
            </div>
            <button className="btn btn-outline" style={{ padding: '4px 8px' }} onClick={() => onRestore(lesson.id)}>
                Восстановить
            </button>
        </div>
    </div>
);