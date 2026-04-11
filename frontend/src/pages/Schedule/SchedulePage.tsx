import { useState, useEffect, useMemo } from "react";
import { useNavigate } from "react-router-dom";
import { dbService } from "@/services/crud";
import { type MappedEvent, DAYS } from "@/types/schedule";
import type { Classroom } from "@/types/classroom";
import "@/styles/Schedule.css";

const SchedulePage = () => {
    const navigate = useNavigate();
    
    // Справочники
    const [classrooms, setClassrooms] = useState<Classroom[]>([]);
    const [groups, setGroups] = useState<any[]>([]);
    const [teachers, setTeachers] = useState<any[]>([]);

    // Фильтры
    const [filterType, setFilterType] = useState<"classroom" | "group" | "teacher">("classroom");
    const [targetId, setTargetId] = useState<string | number>("");
    const [selectedDate, setSelectedDate] = useState(new Date().toISOString().split('T')[0]);
    
    const [events, setEvents] = useState<MappedEvent[]>([]);
    const [loading, setLoading] = useState(false);

    // 1. Загрузка всех справочников при старте
    useEffect(() => {
        const init = async () => {
            try {
                const [roomsData, groupsData, teachersData] = await Promise.all([
                    dbService.list("classrooms"),
                    dbService.list("groups"),
                    dbService.list("teachers")
                ]);
                setClassrooms(roomsData);
                setGroups(groupsData);
                setTeachers(teachersData);
                
                if (roomsData.length > 0) setTargetId(roomsData[0].id);
            } catch (err) {
                console.error("Ошибка загрузки данных:", err);
            }
        };
        init();
    }, []);

    // 2. Вычисление конца недели (Субботы)
    const endOfWeekDate = useMemo(() => {
        const start = new Date(selectedDate);
        const day = start.getDay(); // 0 (Вс) - 6 (Сб)
        const diff = day === 0 ? -1 : 6 - day; // Сколько дней до субботы
        const end = new Date(start);
        end.setDate(start.getDate() + diff);
        return end.toISOString().split('T')[0];
    }, [selectedDate]);

    // 3. Загрузка расписания
    useEffect(() => {
        const fetchSchedule = async () => {
            if (!targetId) return;
            
            setLoading(true);
            try {
                // Выбираем путь в зависимости от типа фильтра
                const apiPath = `schedule/${filterType}`;
                const params = {
                    [`${filterType}_id`]: targetId,
                    date_from: selectedDate,
                    date_to: endOfWeekDate
                };

                const data = await dbService.list(apiPath, params);
                setEvents(data);
            } catch (err) {
                console.error("Ошибка маппера:", err);
                setEvents([]);
            } finally {
                setLoading(false);
            }
        };

        fetchSchedule();
    }, [targetId, filterType, selectedDate, endOfWeekDate]);

    // 4. Группировка событий по датам для вывода заголовков дней
    const groupedEvents = useMemo(() => {
        const groups: { [key: string]: MappedEvent[] } = {};
        events.forEach(event => {
            const dateKey = event.start.split('T')[0];
            if (!groups[dateKey]) groups[dateKey] = [];
            groups[dateKey].push(event);
        });
        // Сортируем даты по порядку
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
                <div className="logo-white" onClick={() => navigate("/schedule")}>КГУ</div>
                <div className="nav-actions">
                    <button className="btn nav-btn" onClick={() => navigate("/profile")}>Профиль</button>
                    <button className="btn nav-btn btn-red" onClick={() => navigate("/login")}>Выход</button>
                </div>
            </nav>

            <div className="filters-container slide-up">
                <div className="filter-group">
                    <label className="filter-label">Тип поиска</label>
                    <select 
                        className="styled-select" 
                        value={filterType}
                        onChange={(e) => {
                            setFilterType(e.target.value as any);
                            setTargetId(""); // сброс при смене типа
                        }}
                    >
                        <option value="classroom">По аудитории</option>
                        <option value="group">По группе</option>
                        <option value="teacher">По преподавателю</option>
                    </select>
                </div>

                <div className="filter-group f-2">
                    <label className="filter-label">Объект</label>
                    <select 
                        className="styled-select" 
                        value={targetId}
                        onChange={(e) => setTargetId(e.target.value)}
                    >
                        <option value="">Выберите из списка...</option>
                        {filterType === "classroom" && classrooms.map(r => <option key={r.id} value={r.id}>{r.num}</option>)}
                        {filterType === "group" && groups.map(g => <option key={g.id} value={g.id}>{g.name}</option>)}
                        {filterType === "teacher" && teachers.map(t => <option key={t.id} value={t.id}>{t.name}</option>)}
                    </select>
                </div>

                <div className="filter-group" style={{ maxWidth: '200px' }}>
                    <label className="filter-label">Дата начала</label>
                    <input type="date" className="input-styled" value={selectedDate} onChange={(e) => setSelectedDate(e.target.value)} />
                </div>
            </div>

            <div className="flex-col pb-40">
                {loading ? (
                    <div className="card text-center mx-2.5">Загрузка расписания...</div>
                ) : groupedEvents.length > 0 ? (
                    groupedEvents.map((group) => (
                        <div key={group.date} className="day-section">
                            {/* Заголовок дня */}
                            <div className="day-header slide-up">
                                {getDayName(group.date)}
                            </div>

                            {group.items.map((mappedItem, index) => {
                                const { start, end, type, extendedProps } = mappedItem;
                                const event = extendedProps.event;
                                const isBooking = type === "3";
                                const isAdjustment = type === "2";

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
                                                        : `${event.type_name || ''} ${event.discipline_name}`
                                                    }
                                                </h4>
                                                <span className={`badge ${isAdjustment ? 'btn-orange' : ''}`} style={{fontSize: '10px'}}>
                                                    {isBooking ? 'БРОНИРОВАНИЕ' : isAdjustment ? 'ЗАМЕНА' : 'ЗАНЯТИЕ'}
                                                </span>
                                            </div>
                                            
                                            <div className="flex-col gap-1">
                                                {!isBooking ? (
                                                    <>
                                                        <div className="details-text">
                                                            👤 {event.teachers_list?.length ? event.teachers_list.join(', ') : 'Преподаватель не указан'}
                                                        </div>
                                                        <div className="details-text">
                                                            👥 Группы: {event.groups_list?.length ? event.groups_list.join(', ') : 'Не указаны'}
                                                        </div>
                                                    </>
                                                ) : (
                                                    <div className="details-text">👤 Ответственный: {event.user_name || '---'}</div>
                                                )}
                                                <div className="details-text">📍 Кабинет: {event.classroom_name}</div>
                                            </div>
                                        </div>
                                    </div>
                                );
                            })}
                        </div>
                    ))
                ) : (
                    <div className="card text-center text-muted mx-2.5">Событий не найдено</div>
                )}
            </div>
        </div>
    );
};

export default SchedulePage;