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
    const [busyEvents, setBusyEvents] = useState<any[]>([]); 
    
    const [selectedDate, setSelectedDate] = useState(new Date().toISOString().split('T')[0]);
    const [startTime, setStartTime] = useState("08:30");
    const [endTime, setEndTime] = useState("10:00");
    const [reason, setReason] = useState("");

    useEffect(() => {
        dbService.list("classrooms").then(setRooms);
    }, []);

    // ЗАГРУЗКА ЗАНЯТОСТИ 
    useEffect(() => {
        const room = rooms.find(r => String(r.id) === selectedRoomId);
        setSelectedRoomObj(room || null);
        
        if (selectedRoomId) {
            const fetchBusy = async () => {
                try {
                    const data = await dbService.list("schedule/classroom", { 
                        classroom_id: selectedRoomId,
                        date: selectedDate 
                    });

                    const formatted = data.map((item: any) => {
                        const isLesson = item.type === "0";
                        const isAdjustment = item.type === "2";
                        const isBooking = item.type === "3";

                        return {
                            title: isBooking ? `БРОНЬ: ${item.extendedProps.event.description}` : item.title,
                            start: item.start, 
                            end: item.end,
                            backgroundColor: isLesson ? '#2c3ab3' : '#e69100',
                            borderColor: 'transparent',
                            editable: false,
                            display: 'block'
                        };
                    });
                    setBusyEvents(formatted);
                } catch (err) {
                    console.error("Ошибка загрузки занятости:", err);
                }
            };
            fetchBusy();
        }
    }, [selectedRoomId, selectedDate, rooms]); 

    const previewEvent = useMemo(() => {
        if (!startTime || !endTime || !selectedRoomId) return [];
        return [{
            id: 'preview',
            title: 'ВАШ ВЫБОР',
            start: `${selectedDate}T${startTime}:00`,
            end: `${selectedDate}T${endTime}:00`,
            backgroundColor: '#2e7d32', 
            borderColor: 'transparent',
            className: 'preview-event-pulse'
        }];
    }, [startTime, endTime, selectedDate, selectedRoomId]);

    const allEvents = [...busyEvents, ...previewEvent];

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
                <div className="flex-row gap-2">
                    <button className="btn nav-btn" onClick={() => navigate("/schedule")}>К расписанию</button>
                    <button className="btn nav-btn" onClick={() => navigate("/profile")}>В профиль</button>
                </div>
            </nav>

            <div className="profile-wrapper flex-row gap-3 align-start p-2" style={{ flex: 1 }}>
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
                        <div className="flex-col f-1">
                            <label className="filter-label">Начало</label>
                            <input 
                                type="time" 
                                step="1800" 
                                className="input-styled"
                                value={startTime}
                                onChange={(e) => setStartTime(e.target.value)}
                            />
                        </div>
                        <div className="flex-col f-1">
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
                            placeholder="Зачем вам аудитория?"
                            style={{ minHeight: '100px' }}
                            value={reason}
                            onChange={(e) => setReason(e.target.value)}
                        />
                    </div>

                    <button 
                        className="btn btn-green mt-2" 
                        onClick={handleBookingSubmit}
                    >
                        Отправить заявку
                    </button>
                </div>

                <div className="card f-1" style={{ minWidth: '500px', height: '80vh' }}>
                    {selectedRoomObj ? (
                        <FullCalendar
                            key={`${selectedRoomId}-${selectedDate}`} 
                            ref={calendarRef}
                            plugins={[timeGridPlugin, interactionPlugin]}
                            initialView="timeGridDay"
                            initialDate={selectedDate}
                            allDaySlot={false}
                            slotDuration="00:30:00" 
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