import { useState} from "react";
import SearchSelect from "@/components/UI/SearchSelect";

interface Props {
    slotId: number;
    onConfirm: (data: any) => void;
    onCancel: () => void;
}

const CreateLessonModal = ({ slotId, onConfirm, onCancel }: Props) => {
    const [formData, setFormData] = useState({
        timeslot: slotId,
        discipline: "" as string | number,
        lesson_type: "" as string | number,
        classroom: "" as string | number,
        teachers: [] as (string | number)[],
        study_groups: [] as (string | number)[]
    });


    const handleConfirm = () => {
        // Простая валидация перед отправкой
        if (!formData.discipline || !formData.lesson_type || !formData.classroom) {
            alert("Пожалуйста, заполните основные поля: дисциплина, тип и аудитория");
            return;
        }
        
        // Преобразуем данные в формат, который ожидает manager.py
        // Твой бэк ожидает списки ID для учителей и групп
        onConfirm(formData);
    };

    return (
        <div className="flex-col gap-2" style={{ minWidth: '450px' }}>
            
            {/* ВЫБОР ДИСЦИПЛИНЫ */}
            <div className="flex-col">
                <label className="filter-label">Дисциплина</label>
                <SearchSelect
                    model="disciplines"
                    value={formData.discipline}
                    onChange={(val) => setFormData({...formData, discipline: val})}
                    placeholder="Найдите дисциплину..."
                />
            </div>

            {/* ВЫБОР ТИПА ЗАНЯТИЯ */}
            <div className="flex-col">
                <label className="filter-label">Тип занятия</label>
                <SearchSelect
                    model="lesson-types"
                    value={formData.lesson_type}
                    onChange={(val) => setFormData({...formData, lesson_type: val})}
                    placeholder="Лекция, практика..."
                />
            </div>

            {/* ВЫБОР АУДИТОРИИ */}
            <div className="flex-col">
                <label className="filter-label">Аудитория</label>
                <SearchSelect
                    model="classrooms"
                    value={formData.classroom}
                    onChange={(val) => setFormData({...formData, classroom: val})}
                    placeholder="Выберите кабинет..."
                />
            </div>

            {/* ВЫБОР ПРЕПОДАВАТЕЛЯ */}
            <div className="flex-col">
                <label className="filter-label">Преподаватели (можно несколько)</label>
                <SearchSelect 
                    model="teachers"
                    isMulti={true} // ВКЛЮЧАЕМ МУЛЬТИВЫБОР
                    value={formData.teachers}
                    onChange={(vals) => setFormData({...formData, teachers: vals})}
                    placeholder="Выберите одного или нескольких..."
                />
            </div>

            {/* ВЫБОР ГРУППЫ */}
            <div className="flex-col">
                <label className="filter-label">Учебные группы (можно несколько)</label>
                <SearchSelect 
                    model="groups"
                    isMulti={true} // ВКЛЮЧАЕМ МУЛЬТИВЫБОР
                    value={formData.study_groups}
                    onChange={(vals) => setFormData({...formData, study_groups: vals})}
                    placeholder="Выберите одну или несколько..."
                />
            </div>

            <div className="flex-row gap-2 mt-3">
                <button className="btn btn-green f-1" onClick={handleConfirm}>
                    Создать занятие
                </button>
                <button className="btn btn-outline f-1" onClick={onCancel}>
                    Отмена
                </button>
            </div>
        </div>
    );
};

export default CreateLessonModal;