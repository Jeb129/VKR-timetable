import { useState, useEffect, useMemo } from "react";
import { useNavigate } from "react-router-dom";
import FullCalendar from "@fullcalendar/react";
import timeGridPlugin from "@fullcalendar/timegrid";
import interactionPlugin from "@fullcalendar/interaction";
import { requestService } from "@/services/request";
import { dbService } from "@/services/crud";
import AsyncSearchSelect from "@/components/UI/SearchSelect";
import { RequestType } from "@/types/enums";
import type { Classroom } from "@/types/classroom";
import "@/styles/Booking.css";

const BookingCreatePage = () => {
    const navigate = useNavigate();

    // Справочники
    const [bookingTypes, setBookingTypes] = useState<any[]>([]);
    const [selectedRoomId, setSelectedRoomId] = useState<number | null>(null);
    const [selectedRoomObj, setSelectedRoomObj] = useState<Classroom | null>(null);
    const [busyEvents, setBusyEvents] = useState<any[]>([]); 

    // Поля формы
    const [selectedDate, setSelectedDate] = useState(new Date().toISOString().split('T')[0]);
    const [startTime, setStartTime] = useState("10:00");
    const [endTime, setEndTime] = useState("11:30");
    const [selectedTypeId, setSelectedTypeId] = useState<string | number>("");
    const [description, setDescription] = useState("");

    // Ошибки и загрузка
    const [formError, setFormError] = useState<string | null>(null);
    const [loading, setLoading] = useState(false);

    // Загрузка типов бронирования
    useEffect(() => {
        dbService.list<any>("booking-types").then(res => {
            setBookingTypes(Array.isArray(res) ? res : res.results || []);
        });
    }, []);

    // Загрузка занятости при смене аудитории/даты
    useEffect(() => {
        if (selectedRoomId) {
            const fetchBusy = async () => {
                try {
                    const data: any = await dbService.list("schedule/classroom", { 
                        classroom_id: selectedRoomId,
                        date: selectedDate 
                    });
                    
                    const formatted = data.map((item: any) => ({
                        title: item.type === "3" ? "ЗАНЯТО (БРОНЬ)" : item.title,
                        start: item.start,
                        end: item.end,
                        backgroundColor: (item.type === "0" || item.type === "2") ? 'var(--p-blue)' : 'var(--p-orange)',
                        borderColor: 'transparent',
                        display: 'block',
                        // Метаданные для валидации наложения
                        timeStart: item.start.split('T')[1].substring(0, 5),
                        timeEnd: item.end.split('T')[1].substring(0, 5)
                    }));
                    setBusyEvents(formatted);
                    
                    // Тянем инфо о корпусе для времени работы
                    const room = await dbService.get<Classroom>("classrooms", selectedRoomId);
                    setSelectedRoomObj(room);
                } catch (err) {
                    console.error("Ошибка загрузки данных аудитории");
                }
            };
            fetchBusy();
        }
    }, [selectedRoomId, selectedDate]);

    // Валидация пересечений
    useEffect(() => {
        setFormError(null);
        if (startTime >= endTime) {
            setFormError("Начало должно быть раньше конца");
            return;
        }
        const hasOverlap = busyEvents.some(ev => startTime < ev.timeEnd && endTime > ev.timeStart);
        if (hasOverlap) {
            setFormError("Выбранное время уже занято");
        }
    }, [startTime, endTime, busyEvents]);

    // Зеленое превью на календаре
    const previewEvent = useMemo(() => {
        if (!selectedRoomId || formError) return [];
        return [{
            id: 'preview',
            title: 'ВАШ ВЫБОР',
            start: `${selectedDate}T${startTime}:00`,
            end: `${selectedDate}T${endTime}:00`,
            backgroundColor: '#2e7d32',
            borderColor: 'transparent',
            className: 'preview-event-pulse'
        }];
    }, [startTime, endTime, selectedDate, selectedRoomId, formError]);

    // Отправка заявки
    const handleSubmit = async () => {
        if (!selectedRoomId || !selectedTypeId || !description) {
            setFormError("Заполните все обязательные поля");
            return;
        }

        setLoading(true);
        try {
            // Формируем полиморфный payload для бэкенда
            const payload = {
                description: description,
                type: 3, // RequestType.BOOKING
                details: {
                    classroom: selectedRoomId,
                    booking_type: selectedTypeId,
                    date_start: `${selectedDate}T${startTime}:00`,
                    date_end: `${selectedDate}T${endTime}:00`
                }
            };

            await requestService.create(payload as any);
            navigate("/profile");
        } catch (err: any) {
            setFormError(err.response?.data?.details?.non_field_errors?.[0] || "Ошибка создания заявки");
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="flex-col bg-main min-h-screen">
            <nav className="navbar">
                <div className="logo-white" onClick={() => navigate("/")} style={{cursor: 'pointer'}}>КГУ • БРОНИРОВАНИЕ</div>
                <button className="btn nav-btn" onClick={() => navigate("/profile")}>В профиль</button>
            </nav>

            <div className="profile-wrapper flex-row gap-3 align-start p-2">
                {/* ЛЕВАЯ ПАНЕЛЬ ФОРМЫ */}
                <div className="card flex-col gap-2" style={{ width: '400px', flexShrink: 0 }}>
                    <h2 className="text-primary">Новое бронирование</h2>
                    
                    <div className="flex-col">
                        <label className="filter-label">Аудитория</label>
                        <AsyncSearchSelect 
                            model="classrooms" 
                            value={selectedRoomId} 
                            onChange={(val) => setSelectedRoomId(Number(val))} 
                            placeholder="Поиск аудитории..."
                        />
                    </div>

                    <div className="flex-col">
                        <label className="filter-label">Дата</label>
                        <input type="date" className="input-styled" value={selectedDate} onChange={e => setSelectedDate(e.target.value)} />
                    </div>

                    <div className="flex-row gap-2">
                        <div className="flex-col f-1">
                            <label className="filter-label">Начало</label>
                            <input type="time" step="900" className="input-styled" value={startTime} onChange={e => setStartTime(e.target.value)} />
                        </div>
                        <div className="flex-col f-1">
                            <label className="filter-label">Конец</label>
                            <input type="time" step="900" className="input-styled" value={endTime} onChange={e => setEndTime(e.target.value)} />
                        </div>
                    </div>

                    <div className="flex-col">
                        <label className="filter-label">Вид мероприятия</label>
                        <select className="styled-select" value={selectedTypeId} onChange={e => setSelectedTypeId(e.target.value)}>
                            <option value="">Выберите тип...</option>
                            {bookingTypes.map(t => <option key={t.id} value={t.id}>{t.name}</option>)}
                        </select>
                    </div>

                    <div className="flex-col">
                        <label className="filter-label">Причина бронирования</label>
                        <textarea 
                            className="input-styled" 
                            rows={3} 
                            value={description} 
                            onChange={e => setDescription(e.target.value)}
                            placeholder="Например: Проведение студенческой конференции"
                        />
                    </div>

                    {formError && <div className="error fade-in" style={{fontSize: '13px'}}>{formError}</div>}

                    <button 
                        className="btn btn-green w-100" 
                        onClick={handleSubmit} 
                        disabled={loading || !!formError}
                    >
                        {loading ? "Отправка..." : "Создать заявку"}
                    </button>
                </div>

                {/* ПРАВАЯ ПАНЕЛЬ С КАЛЕНДАРЕМ */}
                <div className="card f-1" style={{ height: '80vh', minWidth: '600px' }}>
                    {selectedRoomId ? (
                        <FullCalendar
                            key={`${selectedRoomId}-${selectedDate}`}
                            plugins={[timeGridPlugin, interactionPlugin]}
                            initialView="timeGridDay"
                            initialDate={selectedDate}
                            allDaySlot={false}
                            slotDuration="00:30:00"
                            locale="ru"
                            height="100%"
                            headerToolbar={false}
                            events={[...busyEvents, ...previewEvent]}
                            slotMinTime={selectedRoomObj?.work_start || "08:00:00"}
                            slotMaxTime={selectedRoomObj?.work_end || "22:00:00"}
                        />
                    ) : (
                        <div className="flex-col justify-center align-center h-100 text-muted">
                            <h3>Выберите аудиторию</h3>
                            <p>чтобы увидеть свободные временные слоты</p>
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
};

export default BookingCreatePage;