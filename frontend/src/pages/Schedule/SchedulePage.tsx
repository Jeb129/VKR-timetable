import { useState, useEffect } from "react";
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

    // 1. Асинхронная загрузка списка аудиторий
    useEffect(() => {
        const fetchClassrooms = async () => {
            try {
                // подгрузка через ClassroomViewSet 
                const data = await dbService.list("classrooms");
                setClassrooms(data);
                if (data.length > 0) setSelectedRoom(data[0].id);
            } catch (err) {
                console.error("Ошибка при загрузке аудиторий:", err);
            }
        };
        fetchClassrooms();
    }, []);

    // 2. Асинхронная загрузка расписания через маппер
    useEffect(() => {
        const fetchSchedule = async () => {
            if (!selectedRoom) return;
            
            setLoading(true);
            try {
                const data = await dbService.list("schedule/classroom", { 
                    classroom_id: selectedRoom, 
                    date: selectedDate 
                });
                setEvents(data);
            } catch (err) {
                console.error("Ошибка маппера:", err);
                setEvents([]);
            } finally {
                setLoading(false);
            }
        };

        fetchSchedule();
    }, [selectedRoom, selectedDate]);

    // Хелпер для форматирования времени
   const formatTime = (isoString: string) => {
        return new Date(isoString).toLocaleTimeString('ru-RU', { 
            hour: '2-digit', 
            minute: '2-digit',
            timeZone: 'Europe/Moscow' // Принудительно Москва
        });
    };

    return (
        <div className="flex-col bg-main min-h-screen">
            <nav className="navbar">
                <div className="logo-white" onClick={() => navigate("/schedule")}>КГУ</div>
                <div className="nav-actions">
                    <button className="btn nav-btn" onClick={() => navigate("/profile")}>Профиль</button>
                    <button className="btn nav-btn btn-red" onClick={() => navigate("/login")}>Выход</button>
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
                    <input type="date" className="input-styled" value={selectedDate} onChange={(e) => setSelectedDate(e.target.value)} />
                </div>
            </div>

            <div className="flex-col pb-40">
                {loading ? (
                    <div className="card text-center mx-2.5">Загрузка...</div>
                ) : events && events.length > 0 ? (
                    events.map((mappedItem, index) => {
                        // Извлекаем данные по новой структуре
                        const { start, end, type, extendedProps } = mappedItem;
                        const event = extendedProps.event;
                        const isBooking = type === "3";
                        const isAdjustment = type === "2";

                        return (
                            <div key={index} className="lesson-row-container fade-in">
                                <div className={`time-side ${isBooking ? 'bg-orange' : ''}`}>
                                    <span>{formatTime(start)}</span>
                                    <div className="time-line"></div>
                                    <span>{formatTime(end)}</span>
                                </div>

                                <div className="info-side">
                                    <div className="flex-row space-between align-center mb-1">
                                        <h4 className="subject-name">
                                            {isBooking 
                                                ? `Бронь: ${event.description || 'Без описания'}`
                                                : `${event.type_name || ''} ${event.discipline_name}`
                                            }
                                        </h4>
                                        <span className={`badge ${isAdjustment ? 'btn-orange' : ''}`} style={{fontSize: '10px'}}>
                                            {isBooking ? 'БРОНИРОВАНИЕ' : isAdjustment ? 'ЗАМЕНА' : 'ЗАНЯТИЕ'}
                                        </span>
                                    </div>
                                    
                                    <div className="flex-col gap-1">
                                        {!isBooking ? (
                                            <>
                                                <div className="details-text">
                                                    👤 {event.teachers_list?.length ? event.teachers_list.join(', ') : 'Преподаватель не указан'}
                                                </div>
                                                <div className="details-text">
                                                    👥 Группы: {event.groups_list?.length ? event.groups_list.join(', ') : 'Не указаны'}
                                                </div>
                                            </>
                                        ) : (
                                            <div className="details-text">👤 Ответственный: {event.user_name || '---'}</div>
                                        )}
                                        <div className="details-text">📍 Кабинет: {event.classroom_name}</div>
                                    </div>
                                </div>
                            </div>
                        );
                    })
                ) : (
                    <div className="card text-center text-muted mx-2.5">Событий не найдено</div>
                )}
            </div>
        </div>
    );
};

export default SchedulePage;