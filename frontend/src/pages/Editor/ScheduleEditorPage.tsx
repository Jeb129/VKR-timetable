import { useState, useEffect, useRef, useMemo } from "react";
import { type SelectOption } from "@/types/ui";
import SearchSelect from "@/components/UI/SearchSelect";
import { useNavigate,useParams } from "react-router-dom";
import { dbService } from "@/services/crud";
import { DAYS,type Lesson, type Timeslot } from "@/types/schedule";
import "@/styles/Editor.css";
import { scheduleDraftService } from "@/services/schedule_editor";
import LessonErrorItem from "@/components/schedule_editor/LessonError";
import type { ConstraintError, LessonError } from "@/types/constraint";
import { LessonCard } from "@/components/schedule_editor/LessonCard";

const ScheduleEditorPage = () => {
    const { scenarioId } = useParams();
    const navigate = useNavigate();

    // Справочники
    const [scenarios, setScenarios] = useState<any[]>([]);
    const [timeslots, setTimeslots] = useState<Timeslot[]>([]);
    const [groups, setGroups] = useState<any[]>([]);
    const [teachers, setTeachers] = useState<any[]>([]);
    
    // Фильтры
    const [filterType, setFilterType] = useState<"group" | "teacher">("group");
    const [targetId, setTargetId] = useState<string | number>("");
    
    const [currentWeek, setCurrentWeek] = useState<number>(1);

    const [lessonErrors, setLessonErrors] = useState<LessonError[]>([]);
    const [isSidebarOpen, setIsSidebarOpen] = useState(true);

    const [lessons, setLessons] = useState<Lesson[]>([]);
    const [loading, setLoading] = useState(false);
    const [isChecking, setIsChecking] = useState(false);

    const targetOptions: SelectOption[] = useMemo(() => {
        if (filterType === "group") return groups.map(g => ({ value: g.id, label: g.name }));
        if (filterType === "teacher") return teachers.map(t => ({ value: t.id, label: t.name }));
        return [];
    }, [filterType, groups, teachers]);

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
        if (!scenarioId || !targetId) return;
        setLoading(true);
        try {
            const data = filterType === "group" ? 
                await scheduleDraftService.getGroupLessons(Number(scenarioId),Number(targetId)) :
                await scheduleDraftService.getTeacherLessons(Number(scenarioId),Number(targetId))

            setLessons(data || []);
            // накопленные ошибки, записываем сюда
        } catch (err) {
            console.error(err);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => { loadDraft(); }, [scenarioId, targetId, filterType]);

    // Drag and Drop
    const onDragStart = (e: React.DragEvent, lessonId: number) => {
        e.dataTransfer.setData("lessonId", String(lessonId));
    };

    const onDrop = async (e: React.DragEvent, targetTimeslotId: number) => {
        e.preventDefault();

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
            const data = await scheduleDraftService.moveLesson(Number(scenarioId), lessonId, targetTimeslotId )
            const newErrors = lessonErrors.filter(e => e.lesson.id !== lessonId)
            console.log(newErrors)
            if (data.length > 0) {
                const lesson = lessons.find(e => e.id === lessonId)
                if (lesson)
                    newErrors.push({
                        lesson: lesson,
                        errors: data 
                    })
            }
            setLessonErrors(newErrors)
        } catch (err) {
            console.error("Ошибка перемещения");
        }
        finally {
        setIsChecking(false); // Выключаем в любом случае
        }
    };


    const handleCommit = async () => {
        if (!Number(scenarioId)) return;
        try {
            await dbService.commitDraft(Number(scenarioId));
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
                    <button className="btn btn-green" onClick={handleCommit} disabled={!Number(scenarioId)}>Опубликовать</button>
                    <button className="btn nav-btn" onClick={() => navigate("/ScheduleEditor")}>К версиям</button>
                    <button className="btn nav-btn" onClick={() => navigate("/profile")}>В профиль</button>
                </div>
            </nav>

            <div className="editor-container">
                {/* ОСНОВНАЯ ОБЛАСТЬ С ГРИДОМ */}
                <div className="grid-area flex-col gap-2">
                    {/* ПАНЕЛЬ ФИЛЬТРОВ  */}
                    <div className="card flex-row gap-2 align-end" style={{padding: '15px'}}>
                        <div className="flex-col f-1">
                            <label className="filter-label">Тип объекта</label>
                            <select className="styled-select" value={filterType} onChange={e => {setFilterType(e.target.value as any); setTargetId("");}}>
                                <option value="group">Группа</option>
                                <option value="teacher">Преподаватель</option>
                            </select>
                        </div>
                        <div className="flex-col f-2">
                            <label className="filter-label">Объект</label>
                            <SearchSelect 
                                options={targetOptions}
                                value={targetId}
                                onChange={setTargetId}
                            />
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
                                                            <LessonCard lesson={lesson}/>
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
                       {lessonErrors.map((val,i) => 
                            <LessonErrorItem 
                                key={i} 
                                lesson={val.lesson} 
                                errors={val.errors ?? []}
                                />
                       )}
                    </div>
                </div>
            </div>
        </div>
    );
};

export default ScheduleEditorPage;