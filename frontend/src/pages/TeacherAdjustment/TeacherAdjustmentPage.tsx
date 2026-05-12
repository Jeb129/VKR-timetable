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

    // Загрузка справочников
    useEffect(() => {
        const init = async () => {
            const [ts, rooms] = await Promise.all([
                dbService.list("timeslots"),
                dbService.list("classrooms")
            ]);
            setTimeslots(ts);
            setClassrooms(rooms);
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

    const loadSchedule = async () => {
        const teacherId = (user as any)?.teacher_id;
        if (!teacherId) return;
        setLoading(true);
        try {
            const scheduleData = await dbService.list("schedule/teacher/my", {
                date_from: weekDays[0].date,
                date_to: weekDays[5].date
            });
            setEvents(scheduleData);
        } finally { setLoading(false); }
    };

    useEffect(() => { loadSchedule(); }, [selectedDate, user]);

    // --- ЛОГИКА ОТКРЫТИЯ МОДАЛКИ ЧЕРЕЗ КОНТЕКСТ ---
    const openAdjustmentModal = (lesson: any, initialSlotId: number, initialDate: string) => {
        // Создаем локальное состояние для формы ВНУТРИ функции, 
        // которое будет обновляться при перерисовке контента модалки
        // Но в React Context лучше передать отдельный компонент формы.
        
        const AdjustmentForm = () => {
            const [formData, setFormData] = useState({
                date: initialDate,
                timeslot: initialSlotId,
                classroom: lesson.classroom_id || classrooms[0]?.id,
                reason: ""
            });

            const handleSend = async () => {
                if (!formData.reason.trim()) return alert("Укажите причину");
                try {
                    await dbService.create("schedule/adjustment", {
                        lesson_id: lesson.id,
                        timeslot_id: formData.timeslot,
                        date: formData.date,
                        classroom_id: formData.classroom, 
                        description: formData.reason
                    });
                    closeModal();
                    loadSchedule();
                } catch (e) { alert("Ошибка сервера"); }
            };

            return (
                <div className="flex-col gap-2">
                    <div className="flex-col">
                        <label className="filter-label">Дата переноса</label>
                        <input 
                            type="date" 
                            className="input-styled" 
                            value={formData.date}
                            onChange={e => setFormData({...formData, date: e.target.value})}
                        />
                    </div>

                    <div className="flex-col">
                        <label className="filter-label">Время (Таймслот)</label>
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
                        <SearchSelect 
                            options={classrooms.map(c => ({ value: c.id, label: c.num }))}
                            value={formData.classroom}
                            onChange={val => setFormData({...formData, classroom: Number(val)})}
                        />
                    </div>

                    <div className="flex-col">
                        <label className="filter-label">Причина</label>
                        <textarea 
                            className="input-styled" 
                            rows={3}
                            value={formData.reason}
                            onChange={e => setFormData({...formData, reason: e.target.value})}
                        />
                    </div>

                    <button className="btn btn-green w-100 mt-1" onClick={handleSend}>Отправить заявку</button>
                </div>
            );
        };

        openModal({
            title: `Перенос: ${lesson.discipline_name}`,
            width: '550px',
            content: <AdjustmentForm />
        });
    };

    const onDrop = (e: React.DragEvent, slotId: number, date: string) => {
        e.preventDefault();
        const lessonId = Number(e.dataTransfer.getData("lessonId"));
        const lesson = events.find(ev => ev.extendedProps.event.id === lessonId);
        if (lesson) {
            openAdjustmentModal(lesson.extendedProps.event, slotId, date);
        }
    };

    const orderNumbers = Array.from(new Set(timeslots.map(t => t.order_number))).sort();

    return (
        <div className="flex-col bg-main min-h-screen">
            <nav className="navbar">
                <div className="logo-white" onClick={() => navigate("/")}>КГУ • ПЕРЕНОС</div>
                <div className="flex-row gap-2 align-center">
                    <input type="date" className="btn nav-btn" value={selectedDate} onChange={(e) => setSelectedDate(e.target.value)} />
                    <button className="btn nav-btn" onClick={() => navigate("/profile")}>В профиль</button>
                </div>
            </nav>

            <div className="p-3 flex-col gap-2">
                {loading ? <div className="card text-center">Загрузка...</div> : (
                    <div className="card p-0 overflow-x-auto shadow-sm">
                        <table className="editor-grid">
                            <thead>
                                <tr>
                                    <th style={{width: '100px'}}>Пара</th>
                                    {weekDays.map(day => (
                                        <th key={day.id}>{day.name}<br/><small>{new Date(day.date).toLocaleDateString('ru-RU')}</small></th>
                                    ))}
                                </tr>
                            </thead>
                            <tbody>
                                {orderNumbers.map(orderNum => (
                                    <tr key={orderNum}>
                                        <td className="time-cell">
                                            <b>{orderNum}</b>
                                            <div className="time-range">{timeslots.find(t => t.order_number === orderNum)?.time_start.substring(0,5)}</div>
                                        </td>
                                        {weekDays.map(day => {
                                            const weekNum = getISOWeek(new Date(day.date)) % 2 !== 0 ? 1 : 2;
                                            const slot = timeslots.find(t => t.day === day.id && t.order_number === orderNum && t.week_num === weekNum);
                                            const event = events.find(e => e.start.startsWith(day.date) && e.extendedProps.event.order === orderNum);

                                            return (
                                                <td key={day.id} className={`grid-cell ${!slot ? 'disabled' : ''}`}
                                                    onDragOver={e => e.preventDefault()}
                                                    onDrop={e => slot && onDrop(e, slot.id, day.date)}>
                                                    {event ? (
                                                        <div className="draggable-lesson card" draggable 
                                                             onDragStart={e => e.dataTransfer.setData("lessonId", String(event.extendedProps.event.id))}>
                                                            <div className="subject-short">{event.extendedProps.event.discipline_name}</div>
                                                            <div className="info-short">{event.extendedProps.event.classroom_name}</div>
                                                        </div>
                                                    ) : slot && <div className="empty-slot-plus">+</div>}
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