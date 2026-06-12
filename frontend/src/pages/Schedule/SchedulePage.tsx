import { useState, useEffect, useMemo } from "react";
import { useNavigate } from "react-router-dom";
import { type MappedEvent } from "@/types/schedule";
import "@/styles/Schedule.css";
import SearchSelect from "@/components/UI/SearchSelect";
import { scheduleViewService } from "@/services/schedule_view";

const SchedulePage = () => {
    const navigate = useNavigate();

    // Фильтры
    const [filterType, setFilterType] = useState<"classroom" | "group" | "teacher">("classroom");
    const [targetId, setTargetId] = useState<number | null>(null);
    
    const [selectedDate, setSelectedDate] = useState(new Date().toISOString().split('T')[0]);
    const [events, setEvents] = useState<MappedEvent[]>([]);
    const [loading, setLoading] = useState(false);

    // Маппинг типа фильтра на эндпоинты БД для поиска
    const modelMapping = {
        classroom: "classrooms",
        group: "groups",
        teacher: "teachers"
    };

    // Вычисление конца недели (Субботы)
    const endOfWeekDate = useMemo(() => {
        const start = new Date(selectedDate);
        const day = start.getDay(); 
        const diff = day === 0 ? -1 : 6 - day; 
        const end = new Date(start);
        end.setDate(start.getDate() + diff);
        return end.toISOString().split('T')[0];
    }, [selectedDate]);

    // Загрузка расписания
    useEffect(() => {
        const fetchSchedule = async () => {
            if (!targetId) {
                setEvents([]);
                return;
            }
            
            setLoading(true);
            try {
                // Вызываем соответствующий метод сервиса (teacher, group или classroom)
                const data = await scheduleViewService[filterType](
                    targetId, 
                    selectedDate, 
                    endOfWeekDate
                );
                setEvents(data);
            } catch (err) {
                console.error("Ошибка при получении расписания:", err);
                setEvents([]);
            } finally {
                setLoading(false);
            }
        };

        fetchSchedule();
    }, [targetId, filterType, selectedDate, endOfWeekDate]);

    // Группировка событий по датам
    const groupedEvents = useMemo(() => {
        const groups: Record<string, MappedEvent[]> = {};
        events.forEach(event => {
            const dateKey = event.start.split('T')[0];
            if (!groups[dateKey]) groups[dateKey] = [];
            groups[dateKey].push(event);
        });
        return Object.keys(groups).sort().map(date => ({
            date,
            items: groups[date].sort((a, b) => a.start.localeCompare(b.start))
        }));
    }, [events]);

    const formatTime = (isoString: string) => {
        return new Date(isoString).toLocaleTimeString('ru-RU', { 
            hour: '2-digit', 
            minute: '2-digit',
            timeZone: 'Europe/Moscow'
        });
    };

    const getDayName = (dateStr: string) => {
        const date = new Date(dateStr);
        return date.toLocaleDateString('ru-RU', { weekday: 'long', day: 'numeric', month: 'long' });
    };

    return (
        <div className="flex-col bg-main min-h-screen">
            <nav className="navbar">
                <div className="logo-white pointer" onClick={() => navigate("/")}>КГУ</div>
                <div className="nav-actions">
                    <button className="btn nav-btn" onClick={() => navigate("/profile")}>Профиль</button>
                    <button className="btn nav-btn btn-red" onClick={() => navigate("/login")}>Выход</button>
                </div>
            </nav>

            <div className="filters-container slide-up">
                <div className="filter-group">
                    <label className="filter-label">Тип поиска</label>
                    <select 
                        className="select-styled" 
                        value={filterType}
                        onChange={(e) => {
                            setFilterType(e.target.value as any);
                            setTargetId(null);
                        }}
                    >
                        <option value="classroom">По аудитории</option>
                        <option value="group">По группе</option>
                        <option value="teacher">По преподавателю</option>
                    </select>
                </div>

                <div className="filter-group f-2">
                    <label className="filter-label">Объект</label>
                    <SearchSelect 
                        key={filterType}
                        model={modelMapping[filterType]}
                        onChange={(val) => {
                            setTargetId(val);
                        }}
                        placeholder={`Выберите ${
                            filterType === 'classroom' ? 'аудиторию' : 
                            filterType === 'group' ? 'группу' : 
                            filterType === 'teacher' ? 'преподавателя':'тип'
                        }...`}
                    />
                </div>

                <div className="filter-group" style={{ maxWidth: '200px' }}>
                    <label className="filter-label">Дата начала</label>
                    <input 
                        type="date" 
                        className="input-styled" 
                        value={selectedDate} 
                        onChange={(e) => setSelectedDate(e.target.value)} 
                    />
                </div>
            </div>

            <div className="flex-col pb-40 m-2">
                {loading ? (
                    <div className="card text-center">Загрузка расписания...</div>
                ) : groupedEvents.length > 0 ? (
                    groupedEvents.map((group) => (
                        <div key={group.date} className="day-section">
                            <div className="day-header slide-up">
                                {getDayName(group.date)}
                            </div>

                            {group.items.map((mappedItem, index) => {
                                const { start, end, type, extendedProps } = mappedItem;
                                const event = extendedProps.event;
                                
                                const isBooking = String(type) === "3";
                                const isAdjustment = String(type) === "2";
                                const displayClassroom = isBooking ? event.classroom_name : event.classroom;

                                return (
                                    <div key={index} className="lesson-row-container fade-in">
                                        <div className={`time-side ${isBooking ? 'bg-orange' : ''}`}>
                                            <span>{formatTime(start)}</span>
                                            <div className="time-line"></div>
                                            <span>{formatTime(end)}</span>
                                        </div>

                                        <div className="info-side">
                                            <div className="flex-row space-between align-center mb-1">
                                                <h4 className="subject-name">
                                                    {isBooking 
                                                        ? `Бронь: ${event.description || 'Без описания'}`
                                                        : `${event.lesson_type || ''} ${event.discipline || 'Дисциплина не указана'}`
                                                    }
                                                </h4>
                                                <span className={`badge ${isBooking || isAdjustment ? 'badge-pending' : ''}`}>
                                                    {isBooking ? 'БРОНЬ' : isAdjustment ? 'ЗАМЕНА' : 'ЗАНЯТИЕ'}
                                                </span>
                                            </div>
                                            
                                            <div className="flex-col gap-1">
                                                {isBooking ? (
                                                    <>
                                                        <div className="text-muted small">👤 Ответственный: {event.user_name}</div>
                                                        <div className="text-muted small">📝 Цель: {event.description}</div>
                                                    </>
                                                ) : (
                                                    <>
                                                        <div className="text-muted small">
                                                            👤 {event.teachers?.length 
                                                                ? event.teachers.map((t: any) => t.name).join(', ') 
                                                                : 'Преподаватель не указан'}
                                                        </div>
                                                        <div className="text-muted small">
                                                            👥 Группы: {event.study_groups?.length 
                                                                ? event.study_groups.map((g: any) => g.name).join(', ') 
                                                                : 'Не указаны'}
                                                        </div>
                                                    </>
                                                )}
                                                <div className="text-primary font-bold">📍 Кабинет: {displayClassroom || '---'}</div>
                                            </div>
                                        </div>
                                    </div>
                                );
                            })}
                        </div>
                    ))
                ) : (
                    <div className="card text-center text-muted">
                        {targetId ? "Событий не найдено" : "Выберите объект для просмотра расписания"}
                    </div>
                )}
            </div>
        </div>
    );
};

export default SchedulePage;