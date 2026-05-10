import { GridCell } from "@/components/schedule_editor/GridCell";
import { LessonCard } from "@/components/schedule_editor/LessonCard";
import LessonErrorItem from "@/components/schedule_editor/LessonError";
import SearchSelect from "@/components/UI/SearchSelect";
import { useScheduleEditor } from "@/hooks/useScheduleEditor";
import { dbService } from "@/services/crud";
import { scheduleDraftService } from "@/services/schedule_editor";
import "@/styles/Editor.css";
import { DAYS, type Timeslot } from "@/types/schedule";
import { type SelectOption } from "@/types/ui";
import { useCallback, useEffect, useMemo, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";

const ScheduleEditorPage = () => {
    const { scenarioId } = useParams();
    const navigate = useNavigate();

    const { lessons,lessonsLookup,lessonErrors,isChecking,
        loadLessons,moveLesson,setLessons} = useScheduleEditor(Number(scenarioId))

    // Справочники
    // const [scenarios, setScenarios] = useState<any[]>([]);
    const [timeslots, setTimeslots] = useState<Timeslot[]>([]);
    const [groups, setGroups] = useState<any[]>([]);
    const [teachers, setTeachers] = useState<any[]>([]);
    
    // Фильтры
    const [filterType, setFilterType] = useState<"group" | "teacher">("group");
    const [targetId, setTargetId] = useState<string | number>("");
    
    const [currentWeek, setCurrentWeek] = useState<number>(1);

    const [isSidebarOpen, setIsSidebarOpen] = useState(true);

    // const [loading, setLoading] = useState(false);
    // const [isChecking, setIsChecking] = useState(false);
    const [hoveredLessonId, setHoveredLessonId] = useState<string | null>(null);
    const [draggingId, setDraggingId] = useState<string | null>(null);

    const targetOptions: SelectOption[] = useMemo(() => {
        if (filterType === "group") return groups.map(g => ({ value: g.id, label: g.name }));
        if (filterType === "teacher") return teachers.map(t => ({ value: t.id, label: t.name }));
        return [];
    }, [filterType, groups, teachers]);

    useEffect(() => {
        const init = async () => {
            const ts = await dbService.list("timeslots")
            setTimeslots(ts);

            const [ gr, tr] = await Promise.all([
                dbService.list("groups"),
                dbService.list("teachers")
            ]);
            // setScenarios(sc);
            setGroups(gr);
            setTeachers(tr);
        };
        init();
    }, []);

    // Загрузка черновика из Redis
    const loadDraft = async () => {
        if (!scenarioId || !targetId) return;
        // setLoading(true);
        try {
            
            filterType === "group" ? 
                await loadLessons({group_id: Number(targetId), with_errors: true}) :
                await loadLessons({teacher_id: Number(targetId),with_errors: true})
            // накопленные ошибки, записываем сюда
        } catch (err) {
            console.error(err);
        } finally {
            // setLoading(false);
        }
    };

    const handleDelete = async (lessonId: string) => {
    // В черновике удаление — это тоже diff.
    // Если урок draft_created === true, он просто исчезнет.
    // Если урок из основной БД, он пометится как удаленный.
    try {
        await scheduleDraftService.deleteLesson(Number(scenarioId), lessonId);
        // После удаления просто обновляем список уроков
        loadDraft();
    } catch (err) {
        alert("Ошибка при удалении");
    }
};
    useEffect(() => { loadDraft(); }, [targetId, filterType]);

    // Drag and Drop
    const handleDragStart = useCallback((e: React.DragEvent, id: string) => {
        setDraggingId(id);
        e.dataTransfer.setData("lessonId", id);
        // Можно добавить небольшую задержку, чтобы браузер успел создать "призрак" 
        // прежде чем мы сделаем исходную карточку прозрачной
        setTimeout(() => e.target instanceof HTMLElement && (e.target.style.opacity = "0.5"), 0);
    }, []);

    const handleDragEnd = useCallback(() => {
        setDraggingId(null);
    }, []);

    const onDrop = async (lessonId: string, targetSlot: Timeslot) => {
        setDraggingId(null); // Сбрасываем состояние
        
        // Важно: в хуке moveLesson должно быть ОПТИМИСТИЧНОЕ ОБНОВЛЕНИЕ
        // Оно мгновенно переместит урок в массиве lessons, и React перерисует сетку
        await moveLesson(lessonId, targetSlot);
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
                <div className="logo-white" onClick={() => navigate("/")}>КГУ • РЕДАКТОР</div>
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
                                onChange={(e) => setTargetId(e)}
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
                                        <td className="time-cell p-1">
                                            <div className="order-num">{orderNum}</div>
                                            <div className="time-range">
                                                {timeslots.find(t => t.order_number === orderNum)?.time_start.substring(0,5)}
                                            </div>
                                        </td>
                                        {DAYS.map(day => {
                                            // 1. Ищем слот
                                            const slot = timeslots.find(t => 
                                                Number(t.day) === day.id && 
                                                Number(t.order_number) === orderNum && 
                                                Number(t.week_num) === currentWeek
                                            );

                                            // 2. Генерируем ключ для поиска урока (должен совпадать с логикой хука)
                                            const lookupKey = `${day.id}-${orderNum}-${currentWeek}`;
                                            const lesson = lessonsLookup[lookupKey];

                                            // 3. Находим ошибки
                                            const currentErrors = lessonErrors.find(le => le.lesson.id === lesson?.id)?.errors || [];

                                            return (
                                                <GridCell 
                                                    key={day.id}
                                                    slot={slot}
                                                    lesson={lesson}
                                                    errors={currentErrors}
                                                    // isPending={lesson ? pendingIds.has(lesson.id) : false}
                                                    onDragStart={handleDragStart}
                                                    onDragEnd={handleDragEnd}
                                                    onDrop={onDrop}
                                                    onDelete={handleDelete}
                                                    onClick={() => lesson && navigate(`/admin/edit-lesson/${lesson.id}`)}
                                                />
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
                        {
                            lessonErrors?.map((val, i) => (
                                val.errors?.length ?? 0 > 0 ?
                                <LessonErrorItem
                                    key={i}
                                    lesson={val.lesson}
                                    errors={val.errors}
                                /> : <></>
                            ))
                        }
                    </div>
                </div>
            </div>
        </div>
    );
};

export default ScheduleEditorPage;