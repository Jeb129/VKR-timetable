import { useEffect, useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { scheduleDraftService } from "@/services/schedule_editor";
import { dbService } from "@/services/crud";
import { ChangeLogItem } from "@/components/schedule_editor/ChangeLogItem";
import LessonErrorItem from "@/components/schedule_editor/LessonError";
import { DeletedLogItem } from "@/components/schedule_editor/DeletedLogItem";
import type { Lesson } from "@/types/schedule";
import type { LessonError } from "@/types/constraint";
import "@/styles/Editor.css";

const ScenarioReviewPage = () => {
    const { scenarioId } = useParams();
    const navigate = useNavigate();
    const sId = Number(scenarioId);

    const [loading, setLoading] = useState(true);
    const [isApplying, setIsSyncing] = useState(false);
    
    const [scenarioName, setScenarioName] = useState("");
    const [allChanges, setAllChanges] = useState<Lesson[]>([]);
    const [allDeleted, setAllDeleted] = useState<Lesson[]>([]);
    const [globalErrors, setGlobalErrors] = useState<LessonError[]>([]);

    const loadReviewData = async () => {
        setLoading(true);
        try {
            // ОДИН ЗАПРОС вместо трех
            const data = await scheduleDraftService.getSummary(sId);
            
            setGlobalErrors(data.errors);
            setAllChanges(data.changes);
            setAllDeleted(data.deleted);
            
            // Инфо о самом сценарии можно подтянуть отдельно или добавить в summary
            const scenario = await dbService.get("scenarios", sId);
            setScenarioName(scenario.name);
        } catch (err) {
            console.error("Ошибка подготовки ревью:", err);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => { loadReviewData(); }, [sId]);

    const handleApply = async () => {
        setIsSyncing(true);
        try {
            await scheduleDraftService.applyAll(sId);
            // Если все успешно - возвращаемся к списку версий
            navigate("/ScheduleEditor");
        } catch (err) {
            alert("Критическая ошибка при сохранении в БД");
        } finally {
            setIsSyncing(false);
        }
    };

    const handleClear = async () => {
        if (window.confirm("Вы уверены? Все ваши правки в этой версии будут удалены безвозвратно.")) {
            await scheduleDraftService.clearAllDrafts(sId); 
            navigate(`/ScheduleEditor/${sId}`);
        }
    };

    const hasErrors = globalErrors.length > 0;

    return (
        <div className="flex-col bg-main min-h-screen">
            <nav className="navbar">
                <div className="logo-white" onClick={() => navigate("/")}>КГУ • ПРОВЕРКА ВЕРСИИ</div>
                <button className="btn nav-btn" onClick={() => navigate(`/ScheduleEditor/${sId}`)}>Вернуться в редактор</button>
            </nav>

            <div className="profile-wrapper flex-col gap-3" style={{ maxWidth: '1000px', margin: '0 auto' }}>
                
                {/* СТАТУС БЛОК */}
                <div className={`card slide-up ${hasErrors ? 'border-red' : 'border-green'}`} style={{borderWidth: '3px'}}>
                    <div className="flex-row space-between align-center">
                        <div className="flex-col">
                            <h2 className={hasErrors ? 'text-red' : 'text-green'}>
                                {hasErrors ? 'Обнаружены конфликты' : 'Расписание готово к публикации'}
                            </h2>
                            <p className="text-muted">Версия: <b>{scenarioName}</b></p>
                        </div>
                        <div className="flex-row gap-2">
                            <button className="btn btn-outline" onClick={handleClear}>Сбросить черновик</button>
                            <button 
                                className="btn btn-green shadow-lg" 
                                style={{ padding: '15px 30px' }}
                                disabled={isApplying || (allChanges.length === 0 && allDeleted.length === 0)}
                                onClick={handleApply}
                            >
                                {isApplying ? "Синхронизация с БД..." : "Опубликовать изменения"}
                            </button>
                        </div>
                    </div>
                </div>

                <div className="flex-row gap-3 align-start">
                    {/* ЛЕВАЯ КОЛОНКА: ОШИБКИ */}
                    <div className="flex-col f-1 gap-2">
                        <h3 className="text-primary">Конфликты ({globalErrors.length})</h3>
                        <div className="flex-col gap-1">
                            {globalErrors.map((err, i) => (
                                <LessonErrorItem key={i} lesson={err.lesson} errors={err.errors} />
                            ))}
                            {globalErrors.length === 0 && (
                                <div className="card text-center p-4 text-muted">Критические ошибки отсутствуют</div>
                            )}
                        </div>
                    </div>

                    {/* ПРАВАЯ КОЛОНКА: ЛОГ ПРАВОК */}
                    <div className="flex-col f-1 gap-2">
                        <h3 className="text-primary">Изменения ({allChanges.length + allDeleted.length})</h3>
                        <div className="flex-col gap-1">
                            {/* Измененные */}
                            {allChanges.map(l => (
                                <ChangeLogItem key={l.id} lesson={l} onRevert={() => {}} /> 
                            ))}
                            {/* Удаленные */}
                            {allDeleted.map(l => (
                                <DeletedLogItem key={l.id} lesson={l} onRestore={() => {}} />
                            ))}
                            {allChanges.length === 0 && allDeleted.length === 0 && (
                                <div className="card text-center p-4 text-muted">Список правок пуст</div>
                            )}
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default ScenarioReviewPage;