import { useState, useEffect, useRef, useMemo } from "react";
import { useNavigate } from "react-router-dom";
import FullCalendar from "@fullcalendar/react";
import timeGridPlugin from "@fullcalendar/timegrid";
import interactionPlugin from "@fullcalendar/interaction";
import { dbService } from "@/services/crud";
import type { Classroom } from "@/types/classroom";
import "@/styles/Booking.css";

const BookingPage = () => {
    const navigate = useNavigate();
    const calendarRef = useRef<FullCalendar>(null);
    
    const [rooms, setRooms] = useState<Classroom[]>([]);
    const [selectedRoomId, setSelectedRoomId] = useState<string>("");
    const [selectedRoomObj, setSelectedRoomObj] = useState<Classroom | null>(null);
    const [busyEvents, setBusyEvents] = useState<any[]>([]); // Существующие пары
    
    const [selectedDate, setSelectedDate] = useState(new Date().toISOString().split('T')[0]);
    const [startTime, setStartTime] = useState("08:30");
    const [endTime, setEndTime] = useState("10:00");
    const [reason, setReason] = useState("");

    // 1. Загрузка аудиторий
    useEffect(() => {
        dbService.list("classrooms").then(setRooms);
    }, []);

    // 2. Загрузка занятости
    useEffect(() => {
        // Находим объект комнаты
        const room = rooms.find(r => String(r.id) === selectedRoomId);
        setSelectedRoomObj(room || null);
        
        if (selectedRoomId) {
            // Сбрасываем превью при смене комнаты/даты для безопасности
            // Загружаем занятость
            dbService.list("schedule/classroom", { 
                classroom_id: selectedRoomId,
                date: selectedDate 
            }).then(data => {
                const formatted = data.map((item: any) => ({
                    title: item.type === 'lesson' ? 'ЗАНЯТО' : 'БРОНЬ',
                    start: item.date_start,
                    end: item.date_end,
                    backgroundColor: item.type === 'lesson' ? 'var(--p-blue)' : 'var(--p-orange)',
                    borderColor: 'transparent',
                    editable: false
                }));
                setBusyEvents(formatted);
            });

            // Если календарь уже на экране — принудительно переключаем дату
            if (calendarRef.current) {
                const calendarApi = calendarRef.current.getApi();
                calendarApi.gotoDate(selectedDate);
            }
        }
    }, [selectedRoomId, selectedDate, rooms]); 

    // 3. Динамическое превью нашего выбора на календаре
    const previewEvent = useMemo(() => {
        if (!startTime || !endTime) return [];
        return [{
            id: 'preview',
            title: 'ВАШ ВЫБОР',
            start: `${selectedDate}T${startTime}:00`,
            end: `${selectedDate}T${endTime}:00`,
            backgroundColor: '#2e7d32', // не работает если не так 
            borderColor: 'transparent',
            className: 'preview-event-pulse'
        }];
    }, [startTime, endTime, selectedDate]);

    // Собираем все события вместе
    const allEvents = [...busyEvents, ...previewEvent];

    // Кнопка отправки
    const handleBookingSubmit = async () => {
        if (!startTime || !endTime || !reason || !selectedRoomId) {
            return alert("Пожалуйста, заполните все поля!");
        }
        if (startTime >= endTime) {
            return alert("Время начала не может быть позже времени конца");
        }

        try {
            await dbService.create("bookings", {
                classroom: selectedRoomId,
                date_start: `${selectedDate}T${startTime}:00`,
                date_end: `${selectedDate}T${endTime}:00`,
                description: reason
            });
            alert("Заявка успешно отправлена на модерацию!");
            navigate("/profile");
        } catch (err) {
            alert("Ошибка при создании брони. Возможно, это время уже занято.");
        }
    };

    return (
        <div className="flex-col bg-main min-h-screen">
            <nav className="navbar">
                <div className="logo-white" onClick={() => navigate("/schedule")}>КГУ</div>
                <div className="nav-actions">
                    <button className="btn nav-btn" onClick={() => navigate("/schedule")}>К расписанию</button>
                    <button className="btn nav-btn" onClick={() => navigate("/profile")}>В профиль</button>
                </div>
            </nav>

            <div className="profile-wrapper flex-row gap-20 align-start p-2" style={{ flex: 1 }}>
                {/* ЛЕВАЯ ПАНЕЛЬ */}
                <div className="card flex-col gap-2" style={{ width: '380px', flexShrink: 0 }}>
                    <h3 className="text-primary mb-1">Параметры брони</h3>
                    
                    <div className="flex-col">
                        <label className="filter-label">Аудитория</label>
                        <select 
                            className="styled-select" 
                            value={selectedRoomId}
                            onChange={(e) => setSelectedRoomId(e.target.value)}
                        >
                            <option value="">Выберите...</option>
                            {rooms.map(r => <option key={r.id} value={r.id}>{r.num}</option>)}
                        </select>
                    </div>

                    <div className="flex-col">
                        <label className="filter-label">Дата</label>
                        <input 
                            type="date" 
                            className="input-styled" 
                            value={selectedDate}
                            onChange={(e) => setSelectedDate(e.target.value)}
                        />
                    </div>

                    <div className="flex-row gap-2">
                        <div className="flex-col flex-grow">
                            <label className="filter-label">Начало</label>
                            <input 
                                type="time" 
                                step="1800" // Шаг 30 минут
                                className="input-styled"
                                value={startTime}
                                onChange={(e) => setStartTime(e.target.value)}
                            />
                        </div>
                        <div className="flex-col flex-grow">
                            <label className="filter-label">Конец</label>
                            <input 
                                type="time" 
                                step="1800"
                                className="input-styled"
                                value={endTime}
                                onChange={(e) => setEndTime(e.target.value)}
                            />
                        </div>
                    </div>

                    <div className="flex-col">
                        <label className="filter-label">Причина</label>
                        <textarea 
                            className="input-styled" 
                            placeholder="Например: Собрание кафедры"
                            style={{ minHeight: '100px' }}
                            value={reason}
                            onChange={(e) => setReason(e.target.value)}
                        />
                    </div>

                    {/* ГЛАВНАЯ КНОПКА */}
                    <button 
                        className="btn btn-green mt-1" 
                        onClick={handleBookingSubmit}
                    >
                        Отправить заявку
                    </button>
                </div>

                {/* ПРАВАЯ ПАНЕЛЬ С КАЛЕНДАРЕМ */}
                <div className="card f-1" style={{ minWidth: '500px', height: '80vh' }}>
                    {selectedRoomObj ? (
                        <FullCalendar
                            key={`${selectedRoomId}-${selectedDate}`} 
                            ref={calendarRef}
                            plugins={[timeGridPlugin, interactionPlugin]}
                            initialView="timeGridDay"
                            initialDate={selectedDate}
                            allDaySlot={false}
                            slotDuration="00:15:00"
                            slotLabelFormat={{ hour: '2-digit', minute: '2-digit', hour12: false }}
                            locale="ru"
                            height="100%"
                            headerToolbar={false}
                            events={allEvents}
                            slotMinTime={selectedRoomObj.work_start || "08:00:00"}
                            slotMaxTime={selectedRoomObj.work_end || "22:00:00"}
                            selectable={false}
                        />
                    ) : (
                        <div className="flex-col justify-center align-center h-100 text-muted">
                            <h3>Выберите аудиторию</h3>
                            <p>чтобы увидеть график занятости</p>
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
};

export default BookingPage;