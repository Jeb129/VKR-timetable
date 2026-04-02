import React, { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { dbService } from "@/services/crud"; 
import type { MappedEvent } from "@/types/schedule";
import type { Classroom } from "@/types/classroom"; 
import "@/styles/Schedule.css";

const SchedulePage = () => {
    const navigate = useNavigate();
    const [classrooms, setClassrooms] = useState<Classroom[]>([]);
    const [selectedRoom, setSelectedRoom] = useState<string | number>("");
    const [selectedDate, setSelectedDate] = useState(new Date().toISOString().split('T')[0]);
    const [events, setEvents] = useState<MappedEvent[]>([]);
    const [loading, setLoading] = useState(false);

    // 1. Загрузка аудиторий через dbService
    useEffect(() => {
        console.log("Попытка загрузить аудитории..."); // ЛОГ 1
        dbService.list("classrooms")
            .then(data => {
                console.log("Данные получены:", data); // ЛОГ 2
                setClassrooms(data);
                if (data.length > 0) setSelectedRoom(data[0].id);
            })
            .catch(err => {
                console.error("КРИТИЧЕСКАЯ ОШИБКА CRUD:", err); // ЛОГ 3
            });
    }, []);

    // 2. Загрузка расписания (MappedEvents)
    useEffect(() => {
        if (selectedRoom) {
            setLoading(true);
            dbService.list("schedule/classroom", { 
                classroom_id: selectedRoom, 
                date: selectedDate 
            })
            .then(data => setEvents(data))
            .catch(err => console.error("Ошибка маппера:", err))
            .finally(() => setLoading(false));
        }
    }, [selectedRoom, selectedDate]);

    // Функция для красивого вывода времени из ISO строки
    const formatTime = (isoString: string) => {
        const date = new Date(isoString);
        return date.toLocaleTimeString('ru-RU', { hour: '2-digit', minute: '2-digit' });
    };

    return (
        <div className="flex-col bg-main min-h-screen">
            <nav className="navbar">
                <div className="logo-white" onClick={() => navigate("/schedule")}>КГУ</div>
                <div className="flex-row gap-10">
                    <button className="nav-btn" onClick={() => navigate("/profile")}>Профиль</button>
                    <button className="nav-btn" style={{backgroundColor: 'var(--p-red)'}} onClick={() => navigate("/login")}>Выход</button>
                </div>
            </nav>

            <div className="filters-container slide-up">
                <div className="filter-group">
                    <label className="filter-label">Аудитория</label>
                    <select 
                        className="styled-select" 
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
                    <input type="date" className="card p-10" value={selectedDate} onChange={(e) => setSelectedDate(e.target.value)} />
                </div>
            </div>

            <div className="flex-col pb-40">
                {loading ? (
                    <div className="card text-center mx-20">Загрузка расписания...</div>
                ) : events.length > 0 ? (
                    events.map((mappedItem, index) => (
                        <div key={index} className="lesson-row-container fade-in">
                            {/* Время берем из внешних полей маппера */}
                            <div className={`time-side ${mappedItem.type === 'booking' ? 'bg-orange' : ''}`}>
                                <span>{formatTime(mappedItem.date_start)}</span>
                                <div className="time-line"></div>
                                <span>{formatTime(mappedItem.date_end)}</span>
                            </div>

                            <div className="info-side">
                                <div className="flex-row justify-between align-center mb-10">
                                    <h4 className="subject-name">
                                        {mappedItem.type === 'lesson' 
                                            ? `${mappedItem.event.type_name}. ${mappedItem.event.discipline_name}`
                                            : `Бронь: ${mappedItem.event.description}`
                                        }
                                    </h4>
                                </div>
                                
                                <div className="flex-col">
                                    {mappedItem.type === 'lesson' ? (
                                        <>
                                            <div className="details-text">👤 {mappedItem.event.teachers_list?.join(', ')}</div>
                                            <div className="details-text">👥 Группы: {mappedItem.event.groups_list?.join(', ')}</div>
                                        </>
                                    ) : (
                                        <div className="details-text">👤 Ответственный: {mappedItem.event.user_name}</div>
                                    )}
                                    <div className="details-text">📍 Кабинет: {mappedItem.event.classroom_name}</div>
                                </div>
                            </div>
                        </div>
                    ))
                ) : (
                    <div className="card text-center text-muted mx-20">Событий не найдено</div>
                )}
            </div>
        </div>
    );
};

export default SchedulePage;