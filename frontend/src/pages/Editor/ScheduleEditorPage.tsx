import { useState, useEffect, useRef } from "react";
import { useNavigate } from "react-router-dom";
import { dbService } from "@/services/crud";
import type { MappedEvent } from "@/types/schedule";
import { DAYS, type Timeslot } from "@/types/schedule";
import "@/styles/Editor.css";

const ScheduleEditorPage = () => {
    const navigate = useNavigate();
    
    // Справочники
    const [timeslots, setTimeslots] = useState<Timeslot[]>([]);
    const [scenarios, setScenarios] = useState<any[]>([]);
    const [groups, setGroups] = useState<any[]>([]);
    const [teachers, setTeachers] = useState<any[]>([]);
    
    // Состояние фильтров
    const [filterType, setFilterType] = useState<"group" | "teacher">("group");
    const [selectedTargetId, setSelectedTargetId] = useState<string>("");
    const [selectedScenario, setSelectedScenario] = useState("");
    const [currentWeek, setCurrentWeek] = useState<number>(1); // 1 - числитель, 2 - знаменатель
    
    // Данные расписания
    const [events, setEvents] = useState<MappedEvent[]>([]);
    const [loading, setLoading] = useState(false);

    // 1. Костыльные таймслоты (если бэк не отдает список слотов)
    const mockTimeslots: Timeslot[] = [
        { id: 101, day: 1, week_num: 1, order_number: 1, time_start: "08:30:00", time_end: "10:00:00" },
        { id: 102, day: 2, week_num: 1, order_number: 1, time_start: "08:30:00", time_end: "10:00:00" },
        { id: 103, day: 3, week_num: 1, order_number: 2, time_start: "10:10:00", time_end: "11:40:00" },
        // Добавь еще пару штук для теста разных строк и столбцов
    ];

    // 2. Костыльные занятия (MappedEvent)
    const mockEvents: MappedEvent[] = [
        {
            start: "2024-01-01T08:30:00",
            end: "2024-01-01T10:00:00",
            title: "лек. Высшая математика",
            type: "0",
            extendedProps: {
                event: {
                    id: 460,
                    order: 1, // 1-я пара
                    day: 1,   // Понедельник
                    discipline_name: "Высшая математика",
                    type_name: "лек",
                    classroom_name: "Б-407",
                    teachers_list: ["Иванов И.И."],
                    groups_list: ["ПИН-23-1"]
                }
            }
        },
        {
            start: "2024-01-03T10:10:00",
            end: "2024-01-03T11:40:00",
            title: "пр. Базы данных",
            type: "0",
            extendedProps: {
                event: {
                    id: 461,
                    order: 2, // 2-я пара
                    day: 3,   // Среда
                    discipline_name: "Базы данных",
                    type_name: "пр",
                    classroom_name: "Б-201",
                    teachers_list: ["Петров П.П."],
                    groups_list: ["ПИН-23-1"]
                }
            }
        }
    ];

    //const [events, setEvents] = useState<MappedEvent[]>(mockEvents);

    // 1. Инициализация справочников
    useEffect(() => {
        const init = async () => {
            try {
                const ts = await dbService.list("timeslots");
                setTimeslots(ts.length > 0 ? ts : mockTimeslots); // Если бэк пуст - берем костыль
            } catch (e) {
                setTimeslots(mockTimeslots); // Если ошибка - берем костыль
            }
            const [ts, sc, gr, tr] = await Promise.all([
                dbService.list("timeslots"),
                dbService.list("scenarios"),
                dbService.list("groups"),
                dbService.list("teachers")
            ]);
            setTimeslots(ts);
            setScenarios(sc);
            setGroups(gr);
            setTeachers(tr);
        };
        init();
    }, []);

    // 2. Загрузка данных расписания (асинхронно)
    const loadSchedule = async () => {
        if (!selectedTargetId || !selectedScenario) return;
        
        setLoading(true);
        try {
            const path = filterType === "group" ? "schedule/group" : "schedule/teacher";
            const params = {
                [`${filterType}_id`]: selectedTargetId,
                scenario_id: selectedScenario,
                // Для редактора запрашиваем "виртуальный" диапазон, чтобы маппер отдал все пары цикла
                date_from: "2024-01-01", 
                date_to: "2024-01-14"
            };
            const data = await dbService.list(path, params);
            setEvents(data);
            setEvents(data.length > 0 ? data : mockEvents);
        } catch (e) {
            setEvents(mockEvents);
            console.error("Ошибка загрузки данных:", e);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => { loadSchedule(); }, [selectedTargetId, selectedScenario, filterType]);

    // 3. Логика Drag and Drop
    const onDragStart = (e: React.DragEvent, lessonId: number) => {
        e.dataTransfer.setData("lessonId", String(lessonId));
    };

    const onDrop = async (e: React.DragEvent, targetTimeslotId: number) => {
        e.preventDefault();
        const lessonId = e.dataTransfer.getData("lessonId");
        
        try {
            // Отправляем на бэк запрос на перемещение
            await dbService.update("lessons/move", Number(lessonId), {
                timeslot_id: targetTimeslotId,
                scenario_id: selectedScenario
            });
            loadSchedule(); // Обновляем сетку
        } catch (err) {
            alert("Ошибка перемещения: слот занят или возник конфликт");
        }
    };

    const rows = Array.from(new Set(timeslots.map(t => t.order_number))).sort();

    return (
        <div className="flex-col bg-main min-h-screen">
            <nav className="navbar">
                <div className="logo-white">КГУ • РЕДАКТОР</div>
                <div className="flex-row gap-2">
                    <div className="week-switcher flex-row gap-1 p-1 bg-white rounded-md">
                        <button 
                            className={`btn ${currentWeek === 1 ? 'btn-primary' : 'btn-outline'}`}
                            onClick={() => setCurrentWeek(1)}
                        >Числитель</button>
                        <button 
                            className={`btn ${currentWeek === 2 ? 'btn-primary' : 'btn-outline'}`}
                            onClick={() => setCurrentWeek(2)}
                        >Знаменатель</button>
                    </div>
                    <button className="btn nav-btn" onClick={() => navigate("/profile")}>В профиль</button>
                </div>
            </nav>

            <div className="p-2 flex-col gap-2">
                {/* Панель фильтров */}
                <div className="card flex-row gap-2 align-end">
                    <div className="f-1 flex-col">
                        <label className="filter-label">Версия</label>
                        <select className="styled-select" value={selectedScenario} onChange={e => setSelectedScenario(e.target.value)}>
                            <option value="">Выберите сценарий...</option>
                            {scenarios.map(s => <option key={s.id} value={s.id}>{s.name}</option>)}
                        </select>
                    </div>
                    <div className="f-1 flex-col">
                        <label className="filter-label">Тип фильтра</label>
                        <select className="styled-select" value={filterType} onChange={e => {
                            setFilterType(e.target.value as any);
                            setSelectedTargetId("");
                        }}>
                            <option value="group">Группа</option>
                            <option value="teacher">Преподаватель</option>
                        </select>
                    </div>
                    <div className="f-2 flex-col">
                        <label className="filter-label">Объект</label>
                        <select className="styled-select" value={selectedTargetId} onChange={e => setSelectedTargetId(e.target.value)}>
                            <option value="">Выберите из списка...</option>
                            {(filterType === "group" ? groups : teachers).map(item => (
                                <option key={item.id} value={item.id}>{item.name}</option>
                            ))}
                        </select>
                    </div>
                </div>

                {/* Сетка расписания */}
                <div className="card p-0 no-scroll overflow-x-auto shadow-sm">
                    <table className="editor-grid w-100">
                        <thead>
                            <tr>
                                <th style={{width: '100px'}}>Пара</th>
                                {DAYS.map(day => <th key={day.id}>{day.name}</th>)}
                            </tr>
                        </thead>
                        <tbody>
                            {rows.map(orderNum => (
                                <tr key={orderNum}>
                                    <td className="time-cell">
                                        <div className="order-num">{orderNum}</div>
                                        <div className="time-range">
                                            {timeslots.find(t => t.order_number === orderNum)?.time_start.substring(0, 5)}
                                        </div>
                                    </td>
                                    
                                    {DAYS.map(day => {
                                        // Находим нужный Timeslot для этой ячейки
                                        const slot = timeslots.find(t => 
                                            t.day === day.id && 
                                            t.order_number === orderNum && 
                                            t.week_num === currentWeek
                                        );

                                        // Ищем событие, которое попадает в этот слот (по day и order из extendedProps)
                                        const lesson = events.find(e => {
                                            const ev = e.extendedProps.event;
                                            return ev.day == day.id && ev.order == orderNum;
                                        });
                                        if (slot) console.log(`Ячейка: ${day.name}, Пара: ${orderNum}. Найдено:`, lesson);

                                        return (
                                            <td key={day.id} className={`grid-cell ${!slot ? 'disabled' : ''}`}>
                                                {lesson ? (
                                                    <div 
                                                        className="draggable-lesson card"
                                                        draggable
                                                        onDragStart={(e) => onDragStart(e, lesson.extendedProps.event.id)}
                                                    >
                                                        <div className="subject-short">{lesson.extendedProps.event.discipline_name}</div>
                                                        <div className="info-short">
                                                            <span>{lesson.extendedProps.event.classroom_name}</span>
                                                        </div>
                                                    </div>
                                                ) : (
                                                    <div className="empty-slot-plus">+</div>
                                                )}
                                            </td>
                                        );
                                    })}
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
    );
};

export default ScheduleEditorPage;