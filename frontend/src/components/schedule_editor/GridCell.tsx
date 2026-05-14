import React, { memo, useState } from "react";
import { LessonCard } from "./LessonCard";
import { type Lesson, type Timeslot} from "@/types/schedule";
import type { ConstraintError } from "@/types/constraint";

interface GridCellProps {
    slot?: Timeslot;
    lesson?: Lesson;
    errors?: ConstraintError[];
    isPending?: boolean;
    isHighlighted?: boolean;
    isDraggingNow?: boolean; // Тянут ли именно это занятие
    onDrop: (lessonId: string, targetSlot: Timeslot) => void;
    onDragStart: (e: React.DragEvent, id: string) => void;
    onDragEnd: () => void;
    onDelete: (id: string) => void;
    onClick: () => void;
}

export const GridCell = memo(({ 
    slot, 
    lesson, 
    errors, 
    isPending, 
    isHighlighted,
    isDraggingNow,
    onDrop, 
    onDragStart, 
    onDragEnd,
    onDelete,
    onClick 
}: GridCellProps) => {
    const [isOver, setIsOver] = useState(false);

    // Если слота нет в сетке (выходной)
    if (!slot) return <td className="grid-cell disabled"></td>;
    const handleDragOver = (e: React.DragEvent) => {
        e.preventDefault(); // Обязательно для работы Drop
        if (!lesson) setIsOver(true);
    };

    const handleDragLeave = () => setIsOver(false);

    const handleDrop = (e: React.DragEvent) => {
        e.preventDefault();
        setIsOver(false);
        const lessonId = e.dataTransfer.getData("lessonId");
        if (lessonId && lessonId !== lesson?.id) {
            onDrop(lessonId, slot);
        }
    };

    return (
        <td 
            className={`grid-cell ${isOver ? 'drag-over' : ''} ${!lesson ? 'is-empty' : ''}`}
            onDragOver={handleDragOver}
            onDragLeave={handleDragLeave}
            onDrop={handleDrop}
        >
            {lesson ? (
                <div 
                    className={`h-100 ${isDraggingNow ? 'dragging-source' : ''}`}
                    onDragEnd={onDragEnd} // Сбрасываем ID перетаскивания
                >
                    <LessonCard
                        lesson={lesson}
                        errors={errors}
                        isPending={isPending}
                        isHighlighted={isHighlighted}
                        onDragStart={onDragStart}
                        onDelete={() => onDelete(lesson.id)}
                        onClick={onClick}
                    />
                </div>
            ) : (
                <div className="empty-slot-plus flex-row justify-center align-center h-100">
                    +
                </div>
            )}
        </td>
    );
});