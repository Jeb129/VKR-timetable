import { useState, useEffect, useRef, useMemo } from "react";
import { useNavigate } from "react-router-dom";
import FullCalendar from "@fullcalendar/react";
import timeGridPlugin from "@fullcalendar/timegrid";
import interactionPlugin from "@fullcalendar/interaction";
import { dbService } from "@/services/crud";
import type { Classroom } from "@/types/classroom";
import "./Booking.css";

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
                    backgroundColor: item.type === 'lesson' ? '#2c3ab3' : '#e69100',
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
            backgroundColor: '#2e7d32', // Зеленый цвет для выбора
            borderColor: '#1b5e20',
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
                <div className="flex-row gap-10" style={{width: 'auto'}}>
                    <button className="nav-btn" onClick={() => navigate("/schedule")}>К расписанию</button>
                    <button className="nav-btn" onClick={() => navigate("/profile")}>В профиль</button>
                </div>
            </nav>

            <div className="profile-wrapper flex-row gap-20 align-start" style={{ flex: 1, padding: '20px' }}>
                <div className="card flex-col gap-20" style={{ width: '380px', flexShrink: 0 }}>
                    <h3 className="text-primary">Параметры брони</h3>
                    
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
                            className="card" 
                            style={{ padding: '12px', borderRadius: '12px' }}
                            value={selectedDate}
                            onChange={(e) => setSelectedDate(e.target.value)}
                        />
                    </div>

                    <div className="flex-row gap-10">
                        <div className="flex-col flex-grow">
                            <label className="filter-label">Начало</label>
                            <input 
                                type="time" 
                                step="900" // Шаг 15 минут надо увеличить до полу часа или часа
                                className="card"
                                style={{ padding: '10px', borderRadius: '12px' }}
                                value={startTime}
                                onChange={(e) => setStartTime(e.target.value)}
                            />
                        </div>
                        <div className="flex-col flex-grow">
                            <label className="filter-label">Конец</label>
                            <input 
                                type="time" 
                                step="900"
                                className="card"
                                style={{ padding: '10px', borderRadius: '12px' }}
                                value={endTime}
                                onChange={(e) => setEndTime(e.target.value)}
                            />
                        </div>
                    </div>

                    <div className="flex-col">
                        <label className="filter-label">Причина</label>
                        <textarea 
                            className="card" 
                            placeholder="Зачем вам аудитория?"
                            style={{ padding: '12px', minHeight: '80px', borderRadius: '12px' }}
                            value={reason}
                            onChange={(e) => setReason(e.target.value)}
                        />
                    </div>

                    <button 
                        className="primary-btn" 
                        style={{backgroundColor: '#2e7d32'}}
                        onClick={handleBookingSubmit}
                    >
                        Отправить заявку
                    </button>
                </div>

                <div className="card" style={{ flex: 1, minWidth: '500px', height: '80vh' }}>
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
                            // Настройки отображения
                            events={allEvents}
                            slotMinTime={selectedRoomObj.work_start || "08:00:00"}
                            slotMaxTime={selectedRoomObj.work_end || "22:00:00"}
                            selectable={false} // Отключаем выделение мышкой
                        />
                    ) : (
                        <div className="flex-col justify-center align-center h-full text-muted">
                            <h3>Выберите аудиторию</h3>
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
};

export default BookingPage;