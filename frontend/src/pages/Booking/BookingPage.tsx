import { useState, useEffect, useRef, useMemo } from "react";
import { useNavigate } from "react-router-dom";
import FullCalendar from "@fullcalendar/react";
import timeGridPlugin from "@fullcalendar/timegrid";
import interactionPlugin from "@fullcalendar/interaction";
import { dbService } from "@/services/crud";
import SearchSelect from "@/components/UI/SearchSelect";
import type { Classroom } from "@/types/classroom";
import type { SelectOption } from "@/types/ui";
import "@/styles/Booking.css";

const BookingPage = () => {
    const navigate = useNavigate();
    const calendarRef = useRef<FullCalendar>(null);
    
    //справочники
    const [rooms, setRooms] = useState<Classroom[]>([]);
    const [bookingTypes, setBookingTypes] = useState<any[]>([]);

    // Поля для формы
    const [selectedRoomId, setSelectedRoomId] = useState<string | number>("");
    const [selectedTypeId, setSelectedTypeId] = useState<string | number>("");
    const [selectedDate, setSelectedDate] = useState(new Date().toISOString().split('T')[0]);
    const [startTime, setStartTime] = useState("10:00");
    const [endTime, setEndTime] = useState("11:30");
    const [reason, setReason] = useState("");

    const [formError, setFormError] = useState<string | null>(null);
    const [busyEvents, setBusyEvents] = useState<any[]>([]); 
    const [isSubmitting, setIsSubmitting] = useState(false);

    useEffect(() => {
        dbService.list("classrooms").then(setRooms);
    }, []);

    // 1. Загрузка справочников
    useEffect(() => {
        dbService.list("classrooms").then(setRooms);
        dbService.list("booking-types").then(setBookingTypes); // Создай такой эндпоинт на бэке
    }, []);

    const selectedRoomObj = useMemo(() => rooms.find(r => r.id === selectedRoomId), [selectedRoomId, rooms]);

    // 2. Опции для SearchSelect
    const roomOptions: SelectOption[] = useMemo(() => 
        rooms.map(r => ({ value: r.id, label: r.name || r.num })), [rooms]);
    
    const typeOptions: SelectOption[] = useMemo(() => 
        bookingTypes.map(t => ({ value: t.id, label: t.name })), [bookingTypes]);

    // 3. Расчет длительности для резюме
    const durationText = useMemo(() => {
        if (!startTime || !endTime || startTime >= endTime) return null;
        const [h1, m1] = startTime.split(':').map(Number);
        const [h2, m2] = endTime.split(':').map(Number);
        const diffMinutes = (h2 * 60 + m2) - (h1 * 60 + m1);
        const hours = Math.floor(diffMinutes / 60);
        const mins = diffMinutes % 60;
        return `${hours > 0 ? hours + ' ч. ' : ''}${mins > 0 ? mins + ' мин.' : ''}`;
    }, [startTime, endTime]);

    // 4. Загрузка занятости (Уроки + Другие Брони)
    useEffect(() => {
        if (selectedRoomId) {
            const fetchBusy = async () => {
                const data = await dbService.list("schedule/classroom", { 
                    classroom_id: selectedRoomId,
                    date: selectedDate 
                });
                const formatted = data.map((item: any) => ({
                    title: item.type === "3" ? "ЗАНЯТО: БРОНЬ" : item.title,
                    start: item.start, 
                    end: item.end,
                    backgroundColor: item.type === "3" ? 'var(--p-orange)' : 'var(--p-blue)',
                    borderColor: 'transparent',
                    timeStart: item.start.split('T')[1].substring(0, 5),
                    timeEnd: item.end.split('T')[1].substring(0, 5)
                }));
                setBusyEvents(formatted);
            };
            fetchBusy();
        }
    }, [selectedRoomId, selectedDate]);

    // 5. Валидация пересечений
    useEffect(() => {
        setFormError(null);
        if (startTime >= endTime) {
            setFormError("Время начала позже или равно времени конца");
            return;
        }
        const hasOverlap = busyEvents.some(e => startTime < e.timeEnd && endTime > e.timeStart);
        if (hasOverlap) setFormError("Выбранное время пересекается с существующей записью");
    }, [startTime, endTime, busyEvents]);

    const previewEvent = useMemo(() => {
        if (!selectedRoomId || formError) return [];
        return [{
            id: 'preview',
            title: 'ВАШ ВЫБОР',
            start: `${selectedDate}T${startTime}:00`,
            end: `${selectedDate}T${endTime}:00`,
            backgroundColor: 'var(--p-green)', 
            className: 'preview-event-pulse'
        }];
    }, [startTime, endTime, selectedDate, selectedRoomId, formError]);

    const handleBookingSubmit = async () => {
        if (formError || !reason || !selectedRoomId || !selectedTypeId) return;
        try {
            await dbService.create("bookings", {
                classroom: selectedRoomId,
                booking_type: selectedTypeId,
                date_start: `${selectedDate}T${startTime}:00`,
                date_end: `${selectedDate}T${endTime}:00`,
                description: reason
            });
            navigate("/profile");
        } catch (err) { setFormError("Ошибка сервера при создании брони"); }
    };

    return (
        <div className="flex-col bg-main min-h-screen">
            <nav className="navbar">
                <div className="logo-white" onClick={() => navigate("/")}>КГУ</div>
                <div className="nav-actions">
                    <button className="btn nav-btn" onClick={() => navigate("/schedule")}>К расписанию</button>
                    <button className="btn nav-btn" onClick={() => navigate("/profile")}>В профиль</button>
                </div>
            </nav>

            <div className="profile-wrapper flex-row gap-3 align-start p-2">
                {/* ЛЕВАЯ ПАНЕЛЬ ПАРАМЕТРОВ */}
                <div className="card flex-col gap-2" style={{ width: '400px', flexShrink: 0 }}>
                    <h3 className="text-primary">Параметры брони</h3>
                    
                    <div className="flex-col">
                        <label className="filter-label">Аудитория</label>
                        <SearchSelect options={roomOptions} value={selectedRoomId} onChange={setSelectedRoomId} />
                    </div>

                    <div className="flex-col">
                        <label className="filter-label">Тип мероприятия</label>
                        <SearchSelect options={typeOptions} value={selectedTypeId} onChange={setSelectedTypeId} placeholder="Выберите тип..." />
                    </div>

                    <div className="flex-col">
                        <label className="filter-label">Дата</label>
                        <input type="date" className="input-styled" value={selectedDate} onChange={(e) => setSelectedDate(e.target.value)} />
                    </div>

                    <div className="flex-row gap-2">
                        <div className="flex-col f-1">
                            <label className="filter-label">Начало</label>
                            <input type="time" step="1800" className="input-styled" value={startTime} onChange={(e) => setStartTime(e.target.value)} />
                        </div>
                        <div className="flex-col f-1">
                            <label className="filter-label">Конец</label>
                            <input type="time" step="1800" className="input-styled" value={endTime} onChange={(e) => setEndTime(e.target.value)} />
                        </div>
                    </div>

                    <div className="flex-col">
                        <label className="filter-label">Краткое описание</label>
                        <textarea className="input-styled" style={{ minHeight: '80px' }} value={reason} onChange={(e) => setReason(e.target.value)} />
                    </div>

                    {/* БЛОК РЕЗЮМЕ */}
                    {selectedRoomObj && !formError && durationText && (
                        <div className="card p-2 bg-white" style={{ borderStyle: 'dashed', borderColor: 'var(--p-green)' }}>
                            <div style={{ fontSize: '13px' }}>
                                Вы бронируете <strong>{selectedRoomObj.num}</strong> <br/>
                                на <strong>{durationText}</strong>
                            </div>
                        </div>
                    )}

                    {formError && <div className="error text-center" style={{ fontSize: '13px' }}>{formError}</div>}

                    <button className="btn btn-green w-100" onClick={handleBookingSubmit} disabled={!!formError}>
                        Отправить заявку
                    </button>
                </div>

                {/* КАЛЕНДАРЬ */}
                <div className="card f-1" style={{ minWidth: '600px', height: '80vh' }}>
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
                            events={[...busyEvents, ...previewEvent]}
                            slotMinTime={selectedRoomObj.work_start || "08:00:00"}
                            slotMaxTime={selectedRoomObj.work_end || "22:00:00"}
                            selectable={false}
                        />
                    ) : (
                        <div className="flex-col justify-center align-center h-100 text-muted">
                            <h3>Выберите аудиторию для просмотра графика</h3>
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
};

export default BookingPage;