import { useState, useEffect, useMemo } from "react";
import { useNavigate } from "react-router-dom";
import { dbService } from "@/services/crud";
import { useAuth } from "@/context/AuthContext";
import Modal from "@/components/UI/Modal";
import type { MappedEvent, Timeslot } from "@/types/schedule";
import { DAYS } from "@/types/schedule";
import "@/styles/Editor.css";

// Функция для вычисления номера недели (для числителя/знаменателя)
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

    // Данные для сетки
    const [timeslots, setTimeslots] = useState<Timeslot[]>([]);
    const [events, setEvents] = useState<MappedEvent[]>([]);
    const [loading, setLoading] = useState(false);

    // Управление датой (выбор недели)
    const [selectedDate, setSelectedDate] = useState(new Date().toISOString().split('T')[0]);

    // Состояния для модального окна причины
    const [isModalOpen, setIsModalOpen] = useState(false);
    const [reason, setReason] = useState("");
    const [pendingMove, setPendingMove] = useState<{ lessonId: number, slotId: number, date: string } | null>(null);

    const [error, setError] = useState<string | null>(null);

    // 1. Вычисляем даты Пн-Сб для недели, в которую входит selectedDate
    const weekDays = useMemo(() => {
        const current = new Date(selectedDate);
        const day = current.getDay(); 
        const diff = current.getDate() - day + (day === 0 ? -6 : 1); // Находим понедельник
        const monday = new Date(new Date(selectedDate).setDate(diff));

        return DAYS.map((d, index) => {
            const date = new Date(monday);
            date.setDate(monday.getDate() + index);
            return { ...d, date: date.toISOString().split('T')[0] };
        });
    }, [selectedDate]);

    // 2. Загрузка данных (Используем request.user на бэкенде)
    const loadSchedule = async () => {
        if (!user?.internal_user) return;

        setLoading(true);
        try {
            // Запрашиваем справочник слотов
            const tsData = await dbService.list("timeslots");
            setTimeslots(tsData);

            // Запрашиваем расписание текущего пользователя 
            const scheduleData = await dbService.list("schedule/teacher/my", {
                date_from: weekDays[0].date,
                date_to: weekDays[5].date
            });
            setEvents(scheduleData);
        } catch (err) {
            console.error("Ошибка загрузки расписания");
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => { loadSchedule(); }, [selectedDate, user]);

    // 3. Логика Drag-and-Drop
    const onDragStart = (e: React.DragEvent, lessonId: number) => {
        e.dataTransfer.setData("lessonId", String(lessonId));
    };

    const onDrop = (e: React.DragEvent, slotId: number, date: string) => {
        e.preventDefault();
        const lessonId = Number(e.dataTransfer.getData("lessonId"));
        
        setPendingMove({ lessonId, slotId, date });
        setReason("");
        setIsModalOpen(true); 
    };

    const confirmAdjustment = async () => {
        if (!pendingMove || !reason.trim()) {
            setError("Пожалуйста, укажите причину переноса");
            return;
        }
        setError(null); // Сброс старой ошибки

        try {
            await dbService.create("schedule/adjustment", {
                lesson_id: pendingMove.lessonId,
                timeslot_id: pendingMove.slotId,
                date: pendingMove.date,
                description: reason
            });
            setIsModalOpen(false);
            loadSchedule();
        } catch (err: any) {
            setError(err.response?.data?.error || "Сервер отклонил запрос на перенос");
        }
    };

    const orderNumbers = Array.from(new Set(timeslots.map(t => t.order_number))).sort();

    return (
        <div className="flex-col bg-main min-h-screen">
            <nav className="navbar">
                <div className="logo-white" onClick={() => navigate("/schedule")}>КГУ • ПЕРЕНОС</div>
                <div className="flex-row gap-2 align-center">
                    <label className="text-white" style={{fontSize: '14px'}}>Выбор недели:</label>
                    <input 
                        type="date" 
                        className="btn nav-btn" 
                        style={{background: 'white', color: 'var(--p-blue)'}}
                        value={selectedDate}
                        onChange={(e) => setSelectedDate(e.target.value)}
                    />
                    <button className="btn nav-btn" onClick={() => navigate("/profile")}>В профиль</button>
                </div>
            </nav>

            <div className="p-3 flex-col gap-2">
                <div className="card p-0 overflow-x-auto shadow-sm">
                    <table className="editor-grid">
                        <thead>
                            <tr>
                                <th style={{width: '100px'}}>Пара</th>
                                {weekDays.map(day => (
                                    <th key={day.id}>
                                        {day.name} <br/>
                                        <small>{new Date(day.date).toLocaleDateString('ru-RU')}</small>
                                    </th>
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
                                        // Считаем неделю для конкретной даты в столбце
                                        const weekNum = getISOWeek(new Date(day.date)) % 2 !== 0 ? 1 : 2;
                                        
                                        // Ищем слот
                                        const slot = timeslots.find(t => t.day === day.id && t.order_number === orderNum && t.week_num === weekNum);
                                        
                                        // Ищем событие именно на эту дату и этот номер пары
                                        const event = events.find(e => e.start.startsWith(day.date) && e.extendedProps.event.order === orderNum);

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
                                                        onDragStart={e => onDragStart(e, event.extendedProps.event.id)}
                                                    >
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
            </div>

            <Modal 
                isOpen={isModalOpen} 
                onClose={() => setIsModalOpen(false)} 
                title="Заявка на перенос занятия"
                footer={
                    <>
                        <button className="btn btn-green f-1" onClick={confirmAdjustment}>Отправить модератору</button>
                        <button className="btn btn-outline f-1" onClick={() => setIsModalOpen(false)}>Отмена</button>
                    </>
                }
            >
                <div className="flex-col gap-1">
                    {error && <div className="error mb-1 fade-in" style={{fontSize: '13px'}}>{error}</div>}
                    <p className="text-muted" style={{fontSize: '14px'}}>
                        Вы переносите занятие на <strong>{pendingMove ? new Date(pendingMove.date).toLocaleDateString('ru-RU') : ''}</strong>.
                    </p>
                    <label className="filter-label">Укажите причину:</label>
                    <textarea 
                        className="input-styled" 
                        rows={4} 
                        value={reason}
                        onChange={(e) => setReason(e.target.value)}
                        placeholder="Например: Перенос по согласованию с учебной группой..."
                    />
                </div>
            </Modal>
        </div>
    );
};

export default TeacherAdjustmentPage;