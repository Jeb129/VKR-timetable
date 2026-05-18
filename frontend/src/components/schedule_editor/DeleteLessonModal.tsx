import type { Lesson } from "@/types/schedule";

interface Props {
    lesson: Lesson;
    onConfirm: () => void;
    onCancel: () => void;
}

const DeleteLessonModal = ({ lesson, onConfirm, onCancel }: Props) => {
    return (
        <div className="flex-col gap-2">
            <p>Вы действительно хотите удалить это занятие?</p>
            <div className="card bg-main p-2" style={{ border: '1px solid var(--p-red)' }}>
                <strong className="text-primary">{lesson.discipline}</strong>
                <div className="text-muted" style={{ fontSize: '13px' }}>
                    {lesson.classroom} | {lesson.timeslot.time_start.substring(0, 5)}
                </div>
            </div>
            <p className="text-muted" style={{ fontSize: '12px' }}>
                Занятие исчезнет из сетки и переместится в корзину.
            </p>
            <div className="flex-row gap-2 mt-1">
                <button className="btn btn-red f-1" onClick={onConfirm}>Удалить</button>
                <button className="btn btn-outline f-1" onClick={onCancel}>Отмена</button>
            </div>
        </div>
    );
};

export default DeleteLessonModal;