import React, { useState, useEffect } from "react";
import axios from "axios";

interface Lesson {
    id: number;
    discipline_name: string;
    type_name: string;
    classroom_name: string;
    start: string;
    end: string;
    order: number;
    day: number;
    teachers_list: string[];
    groups_list: string[];
}

interface Classroom {
    id: number;
    num: string;
    building?: number;
}

const SchedulePage = () => {
    // 2. Указываем типы в стейтах
    const [classrooms, setClassrooms] = useState<Classroom[]>([]);
    const [selectedRoom, setSelectedRoom] = useState<string | number>("");
    const [selectedDate, setSelectedDate] = useState(new Date().toISOString().split('T')[0]);
    const [lessons, setLessons] = useState<Lesson[]>([]);
    const [loading, setLoading] = useState(false);

    // 3. Загрузка списка аудиторий
    useEffect(() => {
        axios.get("http://localhost:8000/api/classrooms/")
            .then(res => {
                setClassrooms(res.data);
                if (res.data.length > 0) setSelectedRoom(res.data[0].id);
            })
            .catch(err => console.error("Ошибка загрузки аудиторий:", err));
    }, []);

    // 4. Загрузка расписания
    useEffect(() => {
        if (selectedRoom) {
            setLoading(true);
            axios.get(`http://localhost:8000/api/lessons/?classroom_id=${selectedRoom}`)
                .then(res => setLessons(res.data))
                .catch(err => console.error("Ошибка загрузки уроков:", err))
                .finally(() => setLoading(false));
        }
    }, [selectedRoom]);

    return (
        <div className="flex-col bg-main min-h-screen p-20 fade-in">
            
            {/* БЛОК ФИЛЬТРОВ */}
            <div className="flex-row gap-20 mb-20">
                <div className="flex-col flex-grow">
                    <label className="filter-label">Аудитория</label>
                    <select 
                        className="card focus-glow" 
                        style={{ padding: '12px', width: '100%' }}
                        value={selectedRoom}
                        onChange={(e) => setSelectedRoom(e.target.value)}
                    >
                        {classrooms.map(room => (
                            <option key={room.id} value={room.id}>{room.num}</option>
                        ))}
                    </select>
                </div>

                <div className="flex-col" style={{ width: '250px' }}>
                    <label className="filter-label">Дата</label>
                    <input 
                        type="date" 
                        className="card focus-glow"
                        value={selectedDate}
                        onChange={(e) => setSelectedDate(e.target.value)}
                    />
                </div>
            </div>

            {/* ЗАГОЛОВОК ДНЯ */}
            <div className="flex-row justify-between bg-dark-blue p-20 mb-20" style={{ borderRadius: '15px', color: 'white', backgroundColor: '#1a237e' }}>
                <h3 style={{ color: 'white', margin: 0 }}>Расписание</h3>
                <span style={{ fontWeight: 600 }}>{selectedDate}</span>
            </div>

            {/* СПИСОК ЗАНЯТИЙ */}
            <div className="flex-col gap-10 slide-up">
                {loading ? (
                    <div className="card text-center">Загрузка данных...</div>
                ) : lessons.length > 0 ? (
                    lessons.map((lesson) => (
                        <div key={lesson.id} className="flex-row" style={{ alignItems: 'stretch', marginBottom: '15px' }}>
                            
                            {/* Левый блок: Время */}
                            <div className="time-strip flex-col justify-center align-center rounded-left" style={{ backgroundColor: '#2c3ab3', color: 'white', padding: '10px', minWidth: '100px', display: 'flex', alignItems: 'center', justifyContent: 'center', borderRadius: '20px 0 0 20px' }}>
                                <span>{lesson.start}</span>
                                <div style={{ height: '1px', background: 'rgba(255,255,255,0.3)', width: '60%', margin: '5px 0' }}></div>
                                <span>{lesson.end}</span>
                            </div>

                            {/* Правый блок: Контент */}
                            <div className="card flex-grow rounded-right" style={{ borderLeft: 'none', position: 'relative', borderRadius: '0 20px 20px 0' }}>
                                <div className="flex-row justify-between align-center mb-10">
                                    <h4 className="text-primary" style={{ fontSize: '18px', margin: 0, color: '#2c3ab3' }}>
                                        {lesson.type_name}. {lesson.discipline_name}
                                    </h4>
                                    <div style={{ background: '#f0f2f5', padding: '4px 12px', borderRadius: '10px', fontSize: '12px', fontWeight: 600 }}>
                                        {lesson.order}-е занятие
                                    </div>
                                </div>
                                
                                <div className="flex-col gap-10" style={{ color: '#666', fontSize: '14px' }}>
                                    <div className="flex-row align-center gap-10">
                                        <span>👤 {lesson.teachers_list?.length > 0 ? lesson.teachers_list.join(', ') : 'Преподаватель не указан'}</span>
                                    </div>
                                    <div className="flex-row align-center gap-10">
                                        <span>👥 Группы: {lesson.groups_list?.join(', ') || 'Не указаны'}</span>
                                    </div>
                                    <div className="flex-row align-center gap-10">
                                        <span>📍 Аудитория: {lesson.classroom_name}</span>
                                    </div>
                                </div>
                            </div>

                        </div>
                    ))
                ) : (
                    <div className="card text-center text-muted">
                        На выбранную дату занятий не найдено
                    </div>
                )}
            </div>
        </div>
    );
};

export default SchedulePage;