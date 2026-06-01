import { useState } from "react";
import SearchSelect from "@/components/UI/SearchSelect";
import { type SelectOption } from "@/types/ui";
import { type Lesson } from "@/types/schedule";

interface Props {
    lesson: Lesson;
    rooms: any[];
    onConfirm: (roomId: number) => void;
    onCancel: () => void;
}

const EditRoomModal = ({ lesson, rooms, onConfirm, onCancel }: Props) => {
    const [selectedRoom, setSelectedRoom] = useState<string | number>(lesson.classroom);

    const roomOptions: SelectOption[] = rooms.map(r => ({
        value: r.id,
        label: r.name || r.num
    }));

    return (
        <div className="flex-col gap-2">
            <div className="info-group">
                <label className="filter-label">Занятие</label>
                <p><strong>{lesson.discipline}</strong> ({lesson.lesson_type})</p>
            </div>

            <div className="flex-col">
                <label className="filter-label">Выберите новую аудиторию</label>
                <SearchSelect 
                    options={roomOptions}
                    value={selectedRoom}
                    onChange={setSelectedRoom}
                />
            </div>

            <div className="flex-row gap-2 mt-2">
                <button className="btn btn-green f-1" onClick={() => onConfirm(Number(selectedRoom))}>
                    Сохранить
                </button>
                <button className="btn btn-outline f-1" onClick={onCancel}>Отмена</button>
            </div>
        </div>
    );
};

export default EditRoomModal;