import { useState, useEffect, useMemo } from "react";
import { useNavigate } from "react-router-dom";
import FullCalendar from "@fullcalendar/react";
import timeGridPlugin from "@fullcalendar/timegrid";
import interactionPlugin from "@fullcalendar/interaction";
import { requestService } from "@/services/request";
import { dbService } from "@/services/crud";
import SearchSelect from "@/components/UI/SearchSelect";
import type { Classroom } from "@/types/classroom";
import "@/styles/Booking.css";
import { scheduleViewService } from "@/services/schedule_view";
import YandexMap from "@/components/YandexMap";

const BookingCreatePage = () => {
    const navigate = useNavigate();

    // Справочники
    const [, setBookingTypes] = useState<any[]>([]);
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

                    // Тянем инфо о корпусе для времени работы
                    const room = await dbService.get<Classroom>("classrooms", selectedRoomId);
                    console.log(room)
                    setSelectedRoomObj(room);

                    const data: any = await scheduleViewService.classroom(Number(selectedRoomId), selectedDate, selectedDate)

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
                } catch (err) {
                    console.error("Ошибка загрузки данных аудитории");
                }
            };
            fetchBusy();
        }
        else
            setSelectedRoomObj(null);

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
        <div className="flex-col bg-main min-h-screen no-scroll">
            <nav className="navbar">
                <div className="logo-white" onClick={() => navigate("/")}>КГУ • БРОНИРОВАНИЕ</div>
                <button className="btn nav-btn" onClick={() => navigate("/profile")}>В профиль</button>
            </nav>

            <main className="layout-grid p-2">

                <section className="card sidebar flex-col gap-2 scroll-y">
                    <h2 className="text-primary">Место проведения</h2>

                    {/* Содержимое левой панели (аудитория, карта, тип, причина) без изменений */}
                    <div className="flex-col">
                        <label className="filter-label">Аудитория</label>
                        <SearchSelect
                            model="bableclassrooms"
                            value={selectedRoomId}
                            onChange={(val) => setSelectedRoomId(val ? Number(val) : null)}
                            placeholder="Поиск..."
                        />
                    </div>

                    {selectedRoomObj?.building && (
                        <div className="flex-col gap-1">
                            <div>
                                <span className="text-muted">Корпус: </span>
                                <strong className="text-primary">{selectedRoomObj.building.name}</strong>
                            </div>
                            <div>
                                <span className="text-muted">Режим: </span>
                                <span className="text-orange" style={{ fontWeight: 700 }}>
                                    {selectedRoomObj.building.work_start_time.substring(0, 5)} — {selectedRoomObj.building.work_end_time.substring(0, 5)}
                                </span>
                            </div>
                            <div>
                                <span className="text-muted">Адрес: </span>
                                <span>{selectedRoomObj.building.address}</span>
                            </div>
                            <div className="flex-col justify-center align-center mt-1">
                                <YandexMap ymapKey={selectedRoomObj.building.ymap_key ?? ""} />
                            </div>
                        </div>
                    )}

                    <div className="flex-col">
                        <label className="filter-label">Вид мероприятия</label>
                        <SearchSelect model="booking-types" value={selectedTypeId} onChange={setSelectedTypeId} placeholder="Тип..." />
                    </div>

                    <div className="flex-col">
                        <label className="filter-label">Причина</label>
                        <textarea className="input-styled" rows={3} value={description} onChange={e => setDescription(e.target.value)} />
                    </div>

                    {formError && <div className="error">{formError}</div>}

                    <button className="btn btn-green w-100" onClick={handleSubmit} disabled={loading || !!formError}>
                        {loading ? "Отправка..." : "Создать заявку"}
                    </button>
                </section>

                <section className="card f-1 flex-col gap-2 no-scroll">
                    {/* ИСПРАВЛЕННЫЙ БЛОК: Дата и время теперь переносятся на мобилках */}
                    <div className="flex-row gap-2 flex-wrap">
                        <div className="flex-col f-1 min-w-10">
                            <label className="filter-label">Дата</label>
                            <input type="date" className="input-styled" value={selectedDate} onChange={e => setSelectedDate(e.target.value)} />
                        </div>
                        <div className="flex-col f-1 min-w-10">
                            <label className="filter-label">Начало</label>
                            <input type="time" className="input-styled" value={startTime} onChange={e => setStartTime(e.target.value)} />
                        </div>
                        <div className="flex-col f-1 min-w-10">
                            <label className="filter-label">Конец</label>
                            <input type="time" className="input-styled" value={endTime} onChange={e => setEndTime(e.target.value)} />
                        </div>
                    </div>

                    <div className="booking-calendar-holder">
                        {selectedRoomId ? (
                            <FullCalendar
                                key={`${selectedRoomId}-${selectedDate}`}
                                plugins={[timeGridPlugin, interactionPlugin]}
                                initialView="timeGridDay"
                                initialDate={selectedDate}
                                allDaySlot={false}
                                locale="ru"
                                height="auto"
                                headerToolbar={false}
                                events={[...busyEvents, ...previewEvent]}
                                slotMinTime={selectedRoomObj?.work_start || "08:00:00"}
                                slotMaxTime={selectedRoomObj?.work_end || "22:00:00"}
                            />
                        ) : (
                            <div className="flex-col justify-center align-center h-100 text-muted">
                                <h3>Выберите аудиторию</h3>
                            </div>
                        )}
                    </div>
                </section>

            </main>
        </div>
    );
};

export default BookingCreatePage;