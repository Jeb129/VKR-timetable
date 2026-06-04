import { useState, useEffect, useMemo } from "react";
import { useNavigate } from "react-router-dom";
import { dbService } from "@/services/crud";
import { useAuth } from "@/context/AuthContext";
import { useModal } from "@/context/ModalContext";
import SearchSelect from "@/components/UI/SearchSelect";
import type { MappedEvent, Timeslot } from "@/types/schedule";
import type { Classroom } from "@/types/classroom";
import "@/styles/Editor.css";
import { DAYS } from "@/types/enums";

const getISOWeek = (date: Date) => {
    const d = new Date(Date.UTC(date.getFullYear(), date.getMonth(), date.getDate()));
    const dayNum = d.getUTCDay() || 7;
    d.setUTCDate(d.getUTCDate() + 4 - dayNum);
    const yearStart = new Date(Date.UTC(d.getUTCFullYear(), 0, 1));
    return Math.ceil((((d.getTime() - yearStart.getTime()) / 86400000) + 1) / 7);
};

const TeacherAdjustmentPage = () => {
    const { user } = useAuth();
    const navigate = useNavigate();
    const { openModal, closeModal } = useModal();

    const [timeslots, setTimeslots] = useState<Timeslot[]>([]);
    const [classrooms, setClassrooms] = useState<Classroom[]>([]);
    const [events, setEvents] = useState<MappedEvent[]>([]);
    const [selectedDate, setSelectedDate] = useState(new Date().toISOString().split('T')[0]);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);

    // 1. Загрузка справочников
    useEffect(() => {
        const init = async () => {
            try {
                const [ts, rooms] = await Promise.all([
                    dbService.list("timeslots"),
                    dbService.list("classrooms")
                ]);
                setTimeslots(ts);
                setClassrooms(rooms);
            } catch (err) {
                console.error("Ошибка загрузки справочников");
            }
        };
        init();
    }, []);

    const weekDays = useMemo(() => {
        const current = new Date(selectedDate);
        const day = current.getDay(); 
        const diff = current.getDate() - day + (day === 0 ? -6 : 1);
        const monday = new Date(new Date(selectedDate).setDate(diff));
        return DAYS.map((d, index) => {
            const date = new Date(monday);
            date.setDate(monday.getDate() + index);
            return { ...d, date: date.toISOString().split('T')[0] };
        });
    }, [selectedDate]);

    // 2. Загрузка расписания (Бэкенд сам поймет кто это по токену)
    const loadSchedule = async () => {
        if (!user?.internal_user) return;

        setLoading(true);
        setError(null);
        try {
            const scheduleData = await dbService.list("schedule/teacher/my", {
                date_from: weekDays[0].date,
                date_to: weekDays[5].date
            });
            setEvents(scheduleData);
        } catch (err: any) {
            // Если пришла ошибка 500/400 (например, не связан аккаунт)
            setError(err.response?.data?.error || "Профиль преподавателя не связан с аккаунтом");
            setEvents([]);
        } finally { 
            setLoading(false); 
        }
    };

    useEffect(() => { loadSchedule(); }, [selectedDate, user]);

    // --- МОДАЛКА ПЕРЕНОСА ---
    const openAdjustmentModal = (lesson: any, initialSlotId: number, initialDate: string) => {
        const AdjustmentForm = () => {
            const [formData, setFormData] = useState({
                date: initialDate,
                timeslot: initialSlotId,
                classroom: lesson.classroom_id || classrooms[0]?.id,
                reason: ""
            });

            const handleSend = async () => {
                if (!formData.reason.trim()) return alert("Укажите причину переноса");
                try {
                    await dbService.create("schedule/adjustment", {
                        lesson_id: lesson.id,
                        timeslot_id: formData.timeslot,
                        date: formData.date,
                        description: formData.reason
                    });
                    closeModal();
                    loadSchedule();
                } catch (e) { alert("Ошибка при отправке заявки"); }
            };

            return (
                <div className="flex-col gap-2">
                    <div className="flex-col">
                        <label className="filter-label">Дата переноса</label>
                        <input type="date" className="input-styled" value={formData.date} onChange={e => setFormData({...formData, date: e.target.value})} />
                    </div>
                    <div className="flex-col">
                        <label className="filter-label">Время (Пара)</label>
                        <SearchSelect 
                            options={timeslots
                                .filter(t => t.day === (new Date(formData.date).getDay() || 7)) 
                                .map(t => ({ value: t.id, label: `${t.order_number} пара (${t.time_start.substring(0,5)})` }))
                            }
                            value={formData.timeslot}
                            onChange={val => setFormData({...formData, timeslot: Number(val)})}
                        />
                    </div>
                    <div className="flex-col">
                        <label className="filter-label">Аудитория</label>
                        <SearchSelect options={classrooms.map(c => ({ value: c.id, label: c.num }))} value={formData.classroom} onChange={val => setFormData({...formData, classroom: Number(val)})} />
                    </div>
                    <div className="flex-col">
                        <label className="filter-label">Причина</label>
                        <textarea className="input-styled" rows={3} value={formData.reason} onChange={e => setFormData({...formData, reason: e.target.value})} />
                    </div>
                    <button className="btn btn-green w-100 mt-1" onClick={handleSend}>Отправить заявку</button>
                </div>
            );
        };

        openModal({
            title: `Перенос: ${lesson.discipline}`,
            width: '550px',
            content: <AdjustmentForm />
        });
    };

    const onDragStart = (e: React.DragEvent, lessonId: number) => {
        // Записываем ID пары в память браузера на время переноса
        e.dataTransfer.setData("lessonId", String(lessonId));
    };

    const onDrop = (e: React.DragEvent, slotId: number, date: string) => {
        e.preventDefault();
        const lessonId = Number(e.dataTransfer.getData("lessonId"));
        const foundEvent = events.find(ev => ev.extendedProps.event.id === lessonId);
        if (foundEvent) {
            openAdjustmentModal(foundEvent.extendedProps.event, slotId, date);
        }
    };

    const orderNumbers = Array.from(new Set(timeslots.map(t => t.order_number))).sort((a,b) => a-b);

    return (
        <div className="flex-col bg-main min-h-screen">
            <nav className="navbar">
                <div className="logo-white" onClick={() => navigate("/")} style={{cursor: 'pointer'}}>КГУ • ПЕРЕНОС</div>
                <div className="flex-row gap-2 align-center">
                    <input type="date" className="btn nav-btn" style={{background: 'white', color: 'var(--p-blue)'}} value={selectedDate} onChange={(e) => setSelectedDate(e.target.value)} />
                    <button className="btn nav-btn" onClick={() => navigate("/profile")}>В профиль</button>
                </div>
            </nav>

            <div className="p-3 flex-col gap-2">
                {error ? (
                    <div className="card text-center p-4">
                        <h3 className="text-orange">{error}</h3>
                        <p className="text-muted">Убедитесь, что ваш аккаунт связан с преподавателем в базе данных.</p>
                        <button className="btn btn-primary mt-2" onClick={() => navigate("/")}>Вернуться</button>
                    </div>
                ) : loading ? (
                    <div className="card text-center p-4">Загрузка данных...</div>
                ) : (
                    <div className="card p-0 overflow-x-auto shadow-sm">
                        <table className="editor-grid">
                            <thead>
                                <tr>
                                    <th style={{width: '100px'}}>Пара</th>
                                    {weekDays.map(day => (
                                        <th key={day.id}>{day.name}<br/><small>{new Date(day.date).toLocaleDateString('ru-RU', {day: 'numeric', month: 'short'})}</small></th>
                                    ))}
                                </tr>
                            </thead>
                            <tbody>
                                {orderNumbers.map(orderNum => (
                                    <tr key={orderNum}>
                                        <td className="time-cell">
                                            <b>{orderNum}</b>
                                            <div className="time-range">
                                                {timeslots.find(t => t.order_number === orderNum)?.time_start.substring(0, 5)}
                                            </div>
                                        </td>
                                        {weekDays.map(day => {
                                            // 1. Вычисляем чётность недели для текущей даты в колонке
                                            const weekNum = getISOWeek(new Date(day.date)) % 2 !== 0 ? 1 : 2;
                                            
                                            // 2. Ищем доступный таймслот
                                            const slot = timeslots.find(t => 
                                                t.day === day.id && 
                                                t.order_number === orderNum && 
                                                t.week_num === weekNum
                                            );

                                            // 3. ИСПРАВЛЕННЫЙ ПОИСК СОБЫТИЯ
                                            const event = events.find(e => {
                                                const ev = e.extendedProps.event as any;
                                                
                                                // Отрезаем время, оставляем только YYYY-MM-DD
                                                const eventDate = e.start.split('T')[0];
                                                const matchesDate = eventDate === day.date;

                                                // Проверяем номер пары (пробуем все варианты названий полей)
                                                const actualOrder = ev.order || ev.timeslot?.order_number;
                                                const matchesOrder = Number(actualOrder) === Number(orderNum);

                                                return matchesDate && matchesOrder;
                                            });

                                            return (
                                                <td 
                                                    key={day.id} 
                                                    className={`grid-cell ${!slot ? 'disabled' : ''}`}
                                                    onDragOver={e => e.preventDefault()}
                                                    onDrop={e => slot && onDrop(e, slot.id, day.date)}
                                                >
                                                    {event ? (
                                                        <div 
                                                            className="draggable-lesson card" 
                                                            draggable 
                                                            onDragStart={(e) => onDragStart(e, event.extendedProps.event.id)}
                                                        >
                                                            <div className="subject-short">
                                                                {/* Используем discipline или discipline_name */}
                                                                {(event.extendedProps.event as any).discipline || (event.extendedProps.event as any).discipline_name}
                                                            </div>
                                                            <div className="info-short">
                                                                {/* Используем classroom или classroom_name */}
                                                                {(event.extendedProps.event as any).classroom || (event.extendedProps.event as any).classroom_name}
                                                            </div>
                                                        </div>
                                                    ) : (
                                                        slot && <div className="empty-slot-plus">+</div>
                                                    )}
                                                </td>
                                            );
                                        })}
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>
                )}
            </div>
        </div>
    );
};

export default TeacherAdjustmentPage;