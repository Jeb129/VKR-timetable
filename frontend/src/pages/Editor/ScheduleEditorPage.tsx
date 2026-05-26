import { ChangeLogItem } from "@/components/schedule_editor/ChangeLogItem";
import { GridCell } from "@/components/schedule_editor/GridCell";
import LessonErrorItem from "@/components/schedule_editor/LessonError";
import SearchSelect from "@/components/UI/SearchSelect";
import { useModal } from "@/context/ModalContext";
import { DeletedLogItem } from "@/components/schedule_editor/DeletedLogItem";
import DeleteLessonModal from "@/components/schedule_editor/DeleteLessonModal";
import { useScheduleEditor } from "@/hooks/useScheduleEditor";
import { dbService } from "@/services/crud";
import { scheduleDraftService } from "@/services/schedule_editor";
import "@/styles/Editor.css";
import { DAYS } from "@/types/enums";
import { type Timeslot, type Lesson  } from "@/types/schedule";
import { type SelectOption } from "@/types/ui";
import { useCallback, useEffect, useMemo, useState,useRef } from "react";
import { useNavigate, useParams } from "react-router-dom";

const ScheduleEditorPage = () => {
    const { scenarioId } = useParams();
    const navigate = useNavigate();
    const sId = Number(scenarioId);
    const { openModal, closeModal } = useModal();
    
    const { 
        lessonsLookup, 
        lessonErrors, 
        draftChanges,
        isChecking,
        loadLessons,
        swapLessons,
        getLookupKey,     
        moveLesson,
        revertLesson,
        pendingIds // Теперь используем это для индикации на карточках
    } = useScheduleEditor(sId);

    // Справочники
    const [timeslots, setTimeslots] = useState<Timeslot[]>([]);
    const [groups, setGroups] = useState<any[]>([]);
    const [teachers, setTeachers] = useState<any[]>([]);
    const [rooms, setRooms] = useState<any[]>([]);
    
    // Фильтры
    const [filterType, setFilterType] = useState<"group" | "teacher" | "classroom">("group");
    const [targetId, setTargetId] = useState<string | number>("");
    const [currentWeek, setCurrentWeek] = useState<number>(1);
    const [isSidebarOpen, setIsSidebarOpen] = useState(true);
    const [draggingId, setDraggingId] = useState<string | null>(null);

    const [loading, setLoading] = useState(false);

    // Новое состояние для корзины
    const [deletedLessons, setDeletedLessons] = useState<Lesson[]>([]);
    const [activeTab, setActiveTab] = useState<"errors" | "changes" | "trash">("errors");
    
    const switchTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);

    // Функция для запуска таймера переключения недели
    const handleDragOverEdge = (targetWeek: number) => {
        if (currentWeek === targetWeek) return;

        // Если таймер еще не запущен - запускаем
        if (!switchTimerRef.current) {
            switchTimerRef.current = setTimeout(() => {
                setCurrentWeek(targetWeek as 1 | 2);
                switchTimerRef.current = null;
            }, 600); // Задержка 0.6 секунды
        }
    };

    // Очистка таймера, если пользователь увел мышку от края
    const clearSwitchTimer = () => {
        if (switchTimerRef.current) {
            clearTimeout(switchTimerRef.current);
            switchTimerRef.current = null;
        }
    };

    // Очищаем таймер при размонтировании компонента для безопасности
    useEffect(() => {
        return () => clearSwitchTimer();
    }, []);

    // 1. загрузка справочников
    useEffect(() => {
        (async () => {
            const ts = await dbService.list("timeslots")
            setTimeslots(ts);

            const [gr, tr, rm] = await Promise.all([
                dbService.list("groups"),
                dbService.list("teachers"),
                dbService.list("classrooms"), // Добавили аудитории
            ]);
            setGroups(gr);
            setTeachers(tr);
            setRooms(rm);
        })();
    }, []);

    // 2. построение вычислений сетки
    const orderNumbers = useMemo(() => 
        Array.from(new Set(timeslots.map(t => t.order_number))).sort((a,b) => a-b)
    , [timeslots]);

    const timeLookup = useMemo(() => {
        const map: Record<number, string> = {};
        timeslots.forEach(t => {
            if (!map[t.order_number]) map[t.order_number] = t.time_start.substring(0, 5);
        });
        return map;
    }, [timeslots]);

    const targetOptions: SelectOption[] = useMemo(() => {
        if (filterType === "group") return groups.map(g => ({ value: g.id, label: g.name }));
        if (filterType === "teacher") return teachers.map(t => ({ value: t.id, label: t.name }));
        if (filterType === "classroom") return rooms.map(r => ({ value: r.id, label: r.name }));
        return [];
    }, [filterType, groups, teachers, rooms]);

    // 3. Загрузка данных о занятиях
    const loadDraft = useCallback(async () => {
        if (!sId || !targetId) return;

        setLoading(true); 
            const filters: any = { with_errors: true };
            if (filterType === "group") filters.group_id = targetId;
            if (filterType === "teacher") filters.teacher_id = targetId;
            if (filterType === "classroom") filters.classroom_id = targetId;

            const [trashData] = await Promise.all([
                scheduleDraftService.getTrash(sId), // Запрос в корзину
                loadLessons(filters)                
            ]);

            console.log("Удаленные пары подгружены:", trashData);
            setDeletedLessons([...trashData]);

    }, [sId, targetId, filterType, loadLessons]);

    useEffect(() => { loadDraft(); }, [loadDraft]);

    // 4. Обработчики действий
    const onDrop = async (lessonId: string, targetSlot: Timeslot) => {
        setDraggingId(null);

        const lookupKey = getLookupKey(targetSlot)
        // const lookupKey = `${String(targetSlot.day)}-${String(targetSlot.order_number)}-${String(targetSlot.week_num)}`;
        console.log(lookupKey)
        const targetLesson = lessonsLookup[lookupKey];
        if (targetLesson) {
            if (targetLesson.id == lessonId) return;
            console.log("swa lessons")
            await swapLessons(lessonId, targetLesson.id); 
        }
        else
            await moveLesson(lessonId, targetSlot);
    };

    const handleDelete = (lesson: Lesson) => {
        openModal({
            title: "Подтверждение удаления",
            content: (
                <DeleteLessonModal 
                    lesson={lesson} 
                    onConfirm={async () => {
                        try {
                            // Выполняем удаление на сервере
                            await scheduleDraftService.deleteLesson(sId, lesson.id);
                            closeModal();
                            setTimeout(() => loadDraft(), 100);
                            
                        } catch (err) {
                            alert("Не удалось удалить занятие");
                        }
                    }}
                    onCancel={closeModal}
                />
            )
        });
    };

    // 4. Логика восстановления из корзины
    const handleRestore = async (lessonId: string) => {
        await revertLesson(lessonId); // Revert удаляет запись из deleted в Redis
        loadDraft();
    };

    // 5. Публикация 
    const handleCommit = () => {
        // Просто уходим на страницу ревью, передавая ID сценария
        navigate(`/ScheduleEditor/${sId}/review`);
    };

    return (
        <div className="flex-col bg-main min-h-screen">
            <nav className="navbar">
                <div className="logo-white" onClick={() => navigate("/")}>КГУ • РЕДАКТОР</div>
                <div className="flex-row gap-2">
                    <div className="week-switcher flex-row gap-1 bg-white p-1 rounded-md">
                        <button className={`btn ${currentWeek === 1 ? 'btn-primary' : 'btn-outline'}`} onClick={() => setCurrentWeek(1)}>Числитель</button>
                        <button className={`btn ${currentWeek === 2 ? 'btn-primary' : 'btn-outline'}`} onClick={() => setCurrentWeek(2)}>Знаменатель</button>
                    </div>
                    <button className="btn btn-green" onClick={handleCommit} disabled={!sId}>Опубликовать</button>
                    <button className="btn nav-btn" onClick={() => navigate("/ScheduleEditor")}>К версиям</button>
                </div>
            </nav>

            <div className="editor-container">
                <div className="grid-area flex-col gap-2">
                    {/* ПАНЕЛЬ ФИЛЬТРОВ */}
                    <div className="card flex-row gap-2 align-end p-2">
                        <div className="flex-col f-1">
                            <label className="filter-label">Тип объекта</label>
                            <select className="styled-select" value={filterType} onChange={e => {setFilterType(e.target.value as any); setTargetId("");}}>
                                <option value="group">Группа</option>
                                <option value="teacher">Преподаватель</option>
                                <option value="classroom">Аудитория</option>
                            </select>
                        </div>
                        <div className="flex-col f-2">
                            <label className="filter-label">Объект</label>
                            <SearchSelect options={targetOptions} value={targetId} onChange={setTargetId} />
                        </div>
                    </div>

                    {/* МАТРИЦА */}
                    <div className="card p-0 overflow-x-auto shadow-sm" style={{ position: 'relative' }}>
                        <div 
                            className={`drag-edge-zone left ${currentWeek === 2 ? 'active' : ''}`}
                            onDragOver={(e) => { e.preventDefault(); handleDragOverEdge(1); }}
                            onDragLeave={clearSwitchTimer}
                        >
                            <div className="edge-label">ЧИСЛИТЕЛЬ</div>
                        </div>

                        <div 
                            className={`drag-edge-zone right ${currentWeek === 1 ? 'active' : ''}`}
                            onDragOver={(e) => { e.preventDefault(); handleDragOverEdge(2); }}
                            onDragLeave={clearSwitchTimer}
                        >
                            <div className="edge-label">ЗНАМЕНАТЕЛЬ</div>
                        </div>

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
                                            <div className="time-range">{timeLookup[orderNum]}</div>
                                        </td>
                                        {DAYS.map(day => {
                                            const lookupKey = `${day.id}-${orderNum}-${currentWeek}`;
                                            const slot = timeslots.find(t => t.day === day.id && t.order_number === orderNum && t.week_num === currentWeek);
                                            const lesson = lessonsLookup[lookupKey];
                                            const currentErrors = lessonErrors.find(le => le.lesson.id === lesson?.id)?.errors || [];

                                            return (
                                                <GridCell 
                                                    key={lookupKey}
                                                    slot={slot}
                                                    lesson={lesson}
                                                    errors={currentErrors}
                                                    isPending={lesson ? pendingIds.has(lesson.id) : false}
                                                    onDragStart={(e, id) => { setDraggingId(id); e.dataTransfer.setData("lessonId", id); }}
                                                    onDragEnd={() => setDraggingId(null)}
                                                    onDrop={onDrop}
                                                    onDelete={() => lesson && handleDelete(lesson)}
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
                <div className={`error-sidebar ${isSidebarOpen ? '' : 'closed'}`}>
                    {/* Вкладки */}
                    <div className="sidebar-tabs flex-row">
                        <button
                            className={`tab-btn f-1 p-1 ${activeTab === 'errors' ? 'active' : ''}`}
                            onClick={() => setActiveTab('errors')}
                        >
                            Конфликты ({lessonErrors.length})
                        </button>
                        <button
                            className={`tab-btn f-1 p-1 ${activeTab === 'changes' ? 'active' : ''}`}
                            onClick={() => setActiveTab('changes')}
                        >
                            Изменения ({draftChanges.length})
                        </button>
                        <button className={`tab-btn f-1 ${activeTab === 'trash' ? 'active' : ''}`} onClick={() => setActiveTab('trash')}>
                            Корзина ({deletedLessons.length})
                        </button>
                    </div>

                    <div className="flex-col scroll-y f-1 p-2">
                        {activeTab === 'errors' ? (
                            lessonErrors.map((val, i) => (
                                <LessonErrorItem key={i} lesson={val.lesson} errors={val.errors} />
                            ))
                        ) : (
                            draftChanges.map((lesson) => (
                                <ChangeLogItem
                                    key={lesson.id}
                                    lesson={lesson}
                                    onRevert={revertLesson}
                                />
                            ))
                        )}
                        {activeTab === 'trash' && (
                            deletedLessons.length > 0 
                            ? deletedLessons.map(l => <DeletedLogItem key={l.id} lesson={l} onRestore={handleRestore} />)
                            : <div className="text-center p-4 text-muted">Корзина пуста</div>
                        )}

                        {/* Пустые состояния */}
                        {activeTab === 'changes' && draftChanges.length === 0 && (
                            <div className="text-center p-4 text-muted">Нет несохраненных изменений</div>
                        )}
                    </div>
                </div>
            </div>
        </div>
    );
};

export default ScheduleEditorPage;