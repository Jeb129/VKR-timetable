import React, { useState, useEffect } from 'react';
import FullCalendar from '@fullcalendar/react';
import timeGridPlugin from '@fullcalendar/timegrid';
import interactionPlugin from '@fullcalendar/interaction';
import axios from 'axios';
import { useNavigate } from "react-router-dom";
import "./Booking.css";

const BookingPage = () => {
    const navigate = useNavigate();
    const [rooms, setRooms] = useState<any[]>([]);
    const [selectedRoomObj, setSelectedRoomObj] = useState<any>(null);
    const [selectedDate, setSelectedDate] = useState(new Date().toISOString().split('T')[0]);
    const [events, setEvents] = useState([]);

    // 1. Загрузка списка аудиторий
    useEffect(() => {
        axios.get("http://localhost:8000/api/classrooms/").then(res => {
            setRooms(res.data);
        });
    }, []);

    // 2. Функция загрузки занятых слотов
    const loadBusySlots = async (roomId: string, date: string) => {
        try {
            const res = await axios.get(`http://localhost:8000/api/bookings/busy_slots/?classroom_id=${roomId}&date=${date}`);
            const formattedEvents = res.data.map((slot: any) => ({
                title: slot.title || 'Занято',
                start: `${date}T${slot.start}`,
                end: `${date}T${slot.end}`,
                backgroundColor: slot.type === 'lesson' ? '#2c3ab3' : '#e69100',
                borderColor: 'transparent',
                display: 'block',
            }));
            setEvents(formattedEvents);
        } catch (err) {
            console.error("Ошибка загрузки занятости:", err);
        }
    };

    // 3. Следим за изменением комнаты или даты
    useEffect(() => {
        if (selectedRoomObj) {
            loadBusySlots(selectedRoomObj.id, selectedDate);
        }
    }, [selectedRoomObj, selectedDate]);

    const handleSelect = (info: any) => {
        const start = info.startStr.split('T')[1].substring(0, 5);
        const end = info.endStr.split('T')[1].substring(0, 5);
        if (window.confirm(`Забронировать аудиторию на время ${start} - ${end}?`)) {
            // Тут будет логика отправки POST запроса на создание брони
            console.log("Данные для отправки:", {
                classroom: selectedRoomObj.id,
                date_start: info.startStr,
                date_end: info.endStr
            });
        }
    };

    return (
        <div className="flex-col bg-main min-h-screen">
            <nav className="navbar">
                <div className="logo-white" onClick={() => navigate("/schedule")}>КГУ</div>
                <button className="nav-btn" onClick={() => navigate("/profile")}>Назад в профиль</button>
            </nav>

            <div className="profile-wrapper flex-row gap-20">
                {/* Сайдбар */}
                <div className="card" style={{ width: '350px' }}>
                    <h3>Бронирование</h3>
                    <div className="flex-col gap-10 mt-20">
                        <label className="filter-label">Аудитория</label>
                        <select 
                            className="focus-glow p-10" 
                            onChange={e => {
                                const room = rooms.find(r => r.id == e.target.value);
                                setSelectedRoomObj(room);
                            }}
                        >
                            <option value="">Выберите аудиторию...</option>
                            {rooms.map(r => <option key={r.id} value={r.id}>{r.num}</option>)}
                        </select>

                        <label className="filter-label">Дата</label>
                        <input 
                            type="date" 
                            className="card p-10" 
                            value={selectedDate} 
                            onChange={e => setSelectedDate(e.target.value)} 
                        />
                    </div>
                </div>

                {/* Календарь */}
                <div className="flex-grow card" style={{ padding: '10px', height: '80vh', overflow: 'hidden' }}>
                    {selectedRoomObj ? (
                        <FullCalendar
                            plugins={[timeGridPlugin, interactionPlugin]}
                            initialView="timeGridDay"
                            initialDate={selectedDate}
                            allDaySlot={false}
                            slotDuration="00:15:00"
                            slotLabelFormat={{ hour: '2-digit', minute: '2-digit', hour12: false }}
                            locale="ru"
                            slotMinTime={selectedRoomObj.work_start || "08:00:00"}
                            slotMaxTime={selectedRoomObj.work_end || "21:00:00"}
                            selectable={true}
                            selectOverlap={false}
                            events={events}
                            select={handleSelect}
                            headerToolbar={false}
                            height="100%"
                        />
                    ) : (
                        <div className="flex-col justify-center align-center h-full text-muted">
                            Выберите аудиторию для просмотра графика
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
};

export default BookingPage; 