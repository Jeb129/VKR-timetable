import { useState, useEffect, useRef } from "react";
import { useNavigate } from "react-router-dom";
import { dbService } from "@/services/crud";
import type { MappedEvent } from "@/types/schedule";
import { DAYS,type Lesson, type Timeslot } from "@/types/schedule";
import "@/styles/Editor.css";

const ScheduleEditorPage = () => {
    const navigate = useNavigate();

    // Справочники
    const [scenarios, setScenarios] = useState<any[]>([]);
    const [timeslots, setTimeslots] = useState<Timeslot[]>([]);
    const [groups, setGroups] = useState<any[]>([]);
    const [teachers, setTeachers] = useState<any[]>([]);
    
    // Фильтры
    const [selectedScenarioId, setSelectedScenarioId] = useState<number | null>(null);
    const [filterType, setFilterType] = useState<"group" | "teacher">("group");
    const [targetId, setTargetId] = useState<string>("");
    
    const [currentWeek, setCurrentWeek] = useState<number>(1);
    const [lessonErrors, setLessonErrors] = useState<Record<number, string[]>>({});
    const [isSidebarOpen, setIsSidebarOpen] = useState(true);
    const [lessons, setLessons] = useState<Lesson[]>([]);
    const [loading, setLoading] = useState(false);
    const [isChecking, setIsChecking] = useState(false);

    useEffect(() => {
        const init = async () => {
            const [sc, ts, gr, tr] = await Promise.all([
                dbService.list("scenarios"),
                dbService.list("timeslots"),
                dbService.list("groups"),
                dbService.list("teachers")
            ]);
            setScenarios(sc);
            setTimeslots(ts);
            setGroups(gr);
            setTeachers(tr);
        };
        init();
    }, []);

    // Загрузка черновика из Redis
    const loadDraft = async () => {
        if (!selectedScenarioId || !targetId) return;
        setLoading(true);
        try {
            const params = { [filterType === "group" ? "group_id" : "teacher_id"]: targetId };
            const response = await dbService.list(`scenario/${selectedScenarioId}/draft`, params);
            setLessons(response.lessons || []);
            // накопленные ошибки, записываем сюда
        } catch (err) {
            console.error(err);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => { loadDraft(); }, [selectedScenarioId, targetId, filterType]);

    // Drag and Drop
    const onDragStart = (e: React.DragEvent, lessonId: number) => {
        e.dataTransfer.setData("lessonId", String(lessonId));
    };

    const onDrop = async (e: React.DragEvent, targetTimeslotId: number) => {
        e.preventDefault();
        if (!selectedScenarioId) return;

        const lessonId = Number(e.dataTransfer.getData("lessonId"));
        
        // 1. Находим данные целевого слота, чтобы обновить визуализацию немедленно
        const targetSlot = timeslots.find(t => t.id === targetTimeslotId);
        if (!targetSlot) return;

        // 2. обновление
        setLessons(prev => prev.map(l => 
            l.id === lessonId 
            ? { ...l, timeslot: targetTimeslotId, day: targetSlot.day, order: targetSlot.order_number } 
            : l
        ));
        // Включаем статус проверки
        setIsChecking(true);

        try {
            const response = await dbService.updateDraft(selectedScenarioId, lessonId, {
                timeslot: targetTimeslotId
            });
            //console.log("ОШИБКИ ОТ СЕРВЕРА:", response.errors);
            
            if (response.errors && response.errors.length > 0) {
                // Сохраняем только сообщения
                const errorMessages = response.errors.map((e: any) => e.message);
                setLessonErrors(prev => ({ ...prev, [lessonId]: errorMessages }));
                setIsSidebarOpen(true); // Открываем сайдбар если есть реальный конфликт
            } else {
                // Если ошибок нет - чистим старые ошибки для этого занятия
                setLessonErrors(prev => {
                    const newErrors = { ...prev };
                    delete newErrors[lessonId];
                    return newErrors;
                });
            }
            // 3. Синхронизируем с Redis (бэк может вернуть дополнительные правки)
            loadDraft(); 
        } catch (err) {
            console.error("Ошибка перемещения");
            loadDraft(); // Возвращаем как было при ошибке сети
        }
        finally {
        setIsChecking(false); // Выключаем в любом случае
        }
    };

    // Собираем все ошибки в один список для сайдбара
    const allConflicts = Object.entries(lessonErrors).flatMap(([id, errs]) => {
        const lesson = lessons.find(l => l.id === Number(id));
        const disciplineName = lesson ? lesson.discipline_name : `Занятие #${id}`;

        // Фильтруем "OK", если они вдруг просочились с бэка
        return errs
            .filter(msg => msg !== "OK") 
            .map(msg => ({
                lessonId: Number(id),
                disciplineName: disciplineName,
                text: msg
            }));
    });


    const handleCommit = async () => {
        if (!selectedScenarioId) return;
        try {
            await dbService.commitDraft(selectedScenarioId);
            alert("Опубликовано!");
            loadDraft();
        } catch (err) { alert("Ошибка публикации"); }
    };

    const orderNumbers = Array.from(new Set(timeslots.map(t => t.order_number))).sort();

    return (
        <div className="flex-col bg-main min-h-screen">
            <nav className="navbar">
                <div className="logo-white" onClick={() => navigate("/schedule")}>КГУ • РЕДАКТОР</div>
                <div className="flex-row gap-2">
                    <div className="week-switcher flex-row gap-1 bg-white p-1 rounded-md">
                        <button className={`btn ${currentWeek === 1 ? 'btn-primary' : 'btn-outline'}`} onClick={() => setCurrentWeek(1)}>Числитель</button>
                        <button className={`btn ${currentWeek === 2 ? 'btn-primary' : 'btn-outline'}`} onClick={() => setCurrentWeek(2)}>Знаменатель</button>
                    </div>
                    <button className="btn btn-green" onClick={handleCommit} disabled={!selectedScenarioId}>Опубликовать</button>
                    <button className="btn nav-btn" onClick={() => navigate("/profile")}>В профиль</button>
                </div>
            </nav>

            <div className="editor-container">
                {/* ОСНОВНАЯ ОБЛАСТЬ С ГРИДОМ */}
                <div className="grid-area flex-col gap-2">
                    {/* ПАНЕЛЬ ФИЛЬТРОВ  */}
                    <div className="card flex-row gap-2 align-end" style={{padding: '15px'}}>
                        <div className="flex-col f-1">
                            <label className="filter-label">Версия</label>
                            <select className="styled-select" onChange={e => setSelectedScenarioId(Number(e.target.value))}>
                                <option value="">Выберите версию...</option>
                                {scenarios.map(s => <option key={s.id} value={s.id}>{s.name}</option>)}
                            </select>
                        </div>
                        <div className="flex-col f-1">
                            <label className="filter-label">Тип объекта</label>
                            <select className="styled-select" value={filterType} onChange={e => {setFilterType(e.target.value as any); setTargetId("");}}>
                                <option value="group">Группа</option>
                                <option value="teacher">Преподаватель</option>
                            </select>
                        </div>
                        <div className="flex-col f-2">
                            <label className="filter-label">Объект</label>
                            <select className="styled-select" value={targetId} onChange={e => setTargetId(e.target.value)}>
                                <option value="">Выберите из списка...</option>
                                {(filterType === "group" ? groups : teachers).map(item => (
                                    <option key={item.id} value={item.id}>{item.name}</option>
                                ))}
                            </select>
                        </div>
                    </div>

                    {/* МАТРИЦА */}
                    <div className="card p-0 overflow-x-auto shadow-sm">
                        <table className="editor-grid">
                            <thead>
                                <tr>
                                    <th style={{width: '80px'}}>Пара</th>
                                    {DAYS.map(day => <th key={day.id}>{day.name}</th>)}
                                </tr>
                            </thead>
                            <tbody>
                                {orderNumbers.map(orderNum => (
                                    <tr key={orderNum}>
                                        <td className="time-cell">
                                            <b>{orderNum}</b>
                                            <div className="time-range">{timeslots.find(t => t.order_number === orderNum)?.time_start.substring(0,5)}</div>
                                        </td>
                                        {DAYS.map(day => {
                                            const slot = timeslots.find(t => t.day === day.id && t.order_number === orderNum && t.week_num === currentWeek);
                                            const lesson = lessons.find(l => Number(l.day) === day.id && Number(l.order) === orderNum && Number(l.week_num) === currentWeek);
                                            const hasError = lesson ? !!lessonErrors[lesson.id] : false;

                                            return (
                                                <td key={day.id} className={`grid-cell ${!slot ? 'disabled' : ''}`}
                                                    onDragOver={e => e.preventDefault()}
                                                    onDrop={e => slot && onDrop(e, slot.id)}>
                                                    {lesson ? (
                                                        <div className={`draggable-lesson card ${hasError ? 'has-error' : ''}`} 
                                                             draggable onDragStart={e => onDragStart(e, lesson.id)}
                                                             onClick={() => navigate(`/admin/edit-lesson/${lesson.id}`)}>
                                                            {hasError && <div className="error-icon">!</div>}
                                                            <div className="subject-short">{lesson.discipline_name}</div>
                                                            <div className="info-short">
                                                                <span>{lesson.classroom_name}</span>
                                                                <span className="type-tag">{lesson.type_name}</span>
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
                </div>

                {/* САЙДБАР С ЯЗЫЧКОМ */}
                <div className={`error-sidebar ${isSidebarOpen ? '' : 'closed'}`}>
                    {/* Язычок-закладка */}
                    <div className="sidebar-trigger-tab" onClick={() => setIsSidebarOpen(!isSidebarOpen)}>
                        {isSidebarOpen ? '▶' : '⚠️'}
                    </div>

                    <div className="p-2 border-bottom flex-row space-between align-center">
                        <h3 className="text-primary" style={{fontSize: '1rem'}}>Конфликты</h3>
                        <button className="close-sidebar-btn" onClick={() => setIsSidebarOpen(false)}>×</button>
                    </div>

                    {/* Текст о проверке (вместо точки) */}
                    {isChecking && (
                        <div className="checking-banner fade-in">
                            Проверка ограничений...
                        </div>
                    )}

                    <div className="flex-col scroll-y f-1">
                        {allConflicts.length > 0 ? (
                            allConflicts.map((err, i) => (
                                <div key={i} className="error-item fade-in">
                                    {/* Теперь тут название предмета */}
                                    <div className="error-title">{err.disciplineName}</div>
                                    <div className="error-text">{err.text}</div>
                                </div>
                            ))
                        ) : (
                            <div className="p-4 text-center text-muted">
                                {isChecking ? 'Выполняется анализ...' : 'Конфликтов не обнаружено'}
                            </div>
                        )}
                    </div>
                </div>
            </div>
        </div>
    );
};

export default ScheduleEditorPage;