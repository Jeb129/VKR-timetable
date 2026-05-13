// components/schedule_editor/LessonCard.tsx
import type { Lesson} from "@/types/schedule";
import type { ConstraintError } from "@/types/constraint";
import { CollapsibleList } from "@/components/UI/CollapsibleList"
import "@/styles/LessonCard.css";

interface LessonCardProps {
    lesson: Lesson;
    errors?: ConstraintError[];
    isPending?: boolean;
    isHighlighted?: boolean;
    onDragStart?: (e: any, id: string) => void;
    onClick?: () => void;
    onDelete?: () => void;
}

export const LessonCard = ({ 
    lesson, 
    errors = [], 
    isPending = false, 
    onDragStart, 
    onDelete, 
    onClick 
}: LessonCardProps) => {
    
    const hasErrors = errors.length > 0;
    const isHardError = errors.some(e => e.penalty >= 100);
    const isNew = lesson.draft_created;
    const isModified = !isNew && (lesson.draft_diffs?.length ?? 0) > 0;

    const isFieldChanged = (fieldName: string) => 
        lesson.draft_diffs?.some(diff => diff.field === fieldName);

    return (
        <div 
            className={`
                draggable-lesson card p-1 flex-col gap-1
                ${hasErrors ? "has-error" : ""} 
                ${isPending ? "is-pending" : ""}
                ${isNew ? "draft-new" : ""}
                ${isModified ? "draft-modified" : ""}
            `}
            draggable={!isPending}
            onDragStart={e => onDragStart?.(e, lesson.id)}
            onClick={onClick}
        >
            {/* Абсолютно позиционированные индикаторы */}
            <div className="card-indicators flex-row gap-1">
                {isPending ? (
                    <div className="checking-spinner align-center justify-center" title="Проверка...">⏳</div>
                ) : hasErrors && (
                    <div className={`error-icon align-center justify-center ${isHardError ? 'bg-red' : 'bg-orange'}`}>!</div>
                )}
            </div>

            {/* Заголовок */}
            <div className="flex-row space-between align-start w-100">
                <div className={`subject-short truncate f-1 ${isFieldChanged('discipline') ? 'text-orange' : 'text-primary'}`}>
                    {lesson.discipline}
                </div>
                {onDelete && (
                    <button className="delete-btn-mini ml-1" onClick={(e) => { e.stopPropagation(); onDelete(); }}>×</button>
                )}
            </div>

            {/* Преподаватели */}
            <CollapsibleList
                items={lesson.teachers || []}
                containerClassName={isFieldChanged('teachers') ? 'bg-orange-light p-1' : ''}
                renderItem={(t, idx) => (
                    <span className="lesson-card-sub truncate" key={idx}>👤 {t.name}</span>
                )}
            />

            <div className="lesson-divider w-100" />

            {/* Подвал */}
            <div className="flex-row space-between align-center w-100 gap-1">
                <div className={`room-short ${isFieldChanged('classroom') ? 'room-changed' : ''}`}>
                    {lesson.classroom || "—"}
                </div>
                
                <CollapsibleList 
                    items={lesson.study_groups || []}
                    containerClassName={`f-1 justify-end ${isFieldChanged('study_groups') ? 'bg-orange-light' : ''}`}
                    renderItem={(g, idx) => (
                        <span className="lesson-card-meta truncate" key={idx}>{g.name}</span>
                    )}
                />
            </div>
        </div>
    );
};