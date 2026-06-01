import { useState } from "react";
import SearchSelect from "@/components/UI/SearchSelect";
import { type SelectOption } from "@/types/ui";

interface Props {
    slotId: number;
    teachers: any[];
    groups: any[];
    rooms: any[];
    onConfirm: (data: any) => void;
    onCancel: () => void;
}

const CreateLessonModal = ({ slotId, teachers, groups, rooms, onConfirm, onCancel }: Props) => {
    const [formData, setFormData] = useState({
        timeslot: slotId,
        discipline: "", // Здесь в идеале нужен SearchSelect по дисциплинам
        lesson_type: "",
        classroom: "",
        teachers: [] as number[],
        study_groups: [] as number[]
    });

    return (
        <div className="flex-col gap-2" style={{ minWidth: '400px' }}>
            <div className="flex-col">
                <label className="filter-label">Дисциплина (ID)</label>
                <input 
                    className="input-styled" 
                    type="number"
                    onChange={e => setFormData({...formData, discipline: e.target.value})}
                    placeholder="Введите ID дисциплины"
                />
            </div>

            <div className="flex-col">
                <label className="filter-label">Тип (ID)</label>
                <input 
                    className="input-styled" 
                    type="number"
                    onChange={e => setFormData({...formData, lesson_type: e.target.value})}
                    placeholder="Введите ID типа занятия"
                />
            </div>

            <div className="flex-col">
                <label className="filter-label">Аудитория</label>
                <SearchSelect 
                    options={rooms.map(r => ({ value: r.id, label: r.name || r.num }))}
                    value={formData.classroom}
                    onChange={val => setFormData({...formData, classroom: String(val)})}
                />
            </div>

            <div className="flex-row gap-2 mt-2">
                <button className="btn btn-green f-1" onClick={() => onConfirm(formData)}>
                    Создать занятие
                </button>
                <button className="btn btn-outline f-1" onClick={onCancel}>Отмена</button>
            </div>
        </div>
    );
};

export default CreateLessonModal;