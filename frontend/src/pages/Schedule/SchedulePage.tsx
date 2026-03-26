import React, { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import axios from "axios";
import "./Schedule.css"; // Импорт новых стилей

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
    const navigate = useNavigate();
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
        // ОБЯЗАТЕЛЬНО добавляем параметр &date=
        axios.get(`http://localhost:8000/api/lessons/?classroom_id=${selectedRoom}&date=${selectedDate}`)
            .then(res => setLessons(res.data))
            .catch(err => console.error("Ошибка загрузки уроков:", err))
            .finally(() => setLoading(false));
    }
}, [selectedRoom, selectedDate]);

    return (
        <div className="flex-col bg-main min-h-screen">
            
            {/* 1. ВЕРХНЯЯ ПАНЕЛЬ (NAVBAR) */}
            <nav className="navbar">
                <div className="logo-white">КГУ</div>
                <div className="flex-row gap-10">
                    <button className="nav-btn" onClick={() => navigate("/profile")}>Профиль</button>
                    <button className="nav-btn" onClick={() => navigate("/login")}>Выйти</button>
                </div>
            </nav>

            {/* 2. ФИЛЬТРЫ */}
            <div className="filters-container slide-up">
                <div className="filter-group">
                    <label className="filter-label">Аудитория</label>
                    <select 
                        className="focus-glow" 
                        style={{ padding: '12px', borderRadius: '12px', border: '1px solid #ddd' }}
                        value={selectedRoom}
                        onChange={(e) => setSelectedRoom(e.target.value)}
                    >
                        {classrooms.map(room => (
                            <option key={room.id} value={room.id}>{room.num}</option>
                        ))}
                    </select>
                </div>

                <div className="filter-group" style={{ maxWidth: '250px' }}>
                    <label className="filter-label">Дата</label>
                    <input 
                        type="date" 
                        className="focus-glow"
                        value={selectedDate}
                        onChange={(e) => setSelectedDate(e.target.value)}
                    />
                </div>
            </div>

            {/* 3. СПИСОК ЗАНЯТИЙ */}
            <div className="flex-col pb-40">
                {loading ? (
                    <div className="card text-center" style={{margin: '0 20px'}}>Загрузка...</div>
                ) : lessons.length > 0 ? (
                    lessons.map((lesson) => (
                        <div key={lesson.id} className="lesson-row-container fade-in">
                            
                            {/* Время */}
                            <div className="time-side">
                                <span>{lesson.start}</span>
                                <div className="time-line"></div>
                                <span>{lesson.end}</span>
                            </div>

                            {/* Информация */}
                            <div className="info-side">
                                <div className="flex-row justify-between align-center mb-10">
                                    <h4 className="subject-name">
                                        {lesson.type_name}. {lesson.discipline_name}
                                    </h4>
                                    <div className="order-badge">
                                        {lesson.order}-е занятие
                                    </div>
                                </div>
                                
                                <div className="flex-col">
                                    <div className="details-text">
                                        👤 {lesson.teachers_list?.length > 0 ? lesson.teachers_list.join(', ') : 'Преподаватель не указан'}
                                    </div>
                                    <div className="details-text">
                                        👥 Группы: {lesson.groups_list?.join(', ') || 'Не указаны'}
                                    </div>
                                    <div className="details-text">
                                        📍 Аудитория: {lesson.classroom_name}
                                    </div>
                                </div>
                            </div>
                        </div>
                    ))
                ) : (
                    <div className="card text-center text-muted" style={{margin: '0 20px'}}>
                        Занятий на выбранный день не найдено
                    </div>
                )}
            </div>
        </div>
    );
};

export default SchedulePage;