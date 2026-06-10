import { useState, useEffect, useRef } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { dbService } from "@/services/crud";
import { scheduleDraftService } from "@/services/schedule_editor";
import "@/styles/Generator.css";

const formatSeconds = (totalSeconds: number) => {
    const hours = Math.floor(totalSeconds / 3600);
    const minutes = Math.floor((totalSeconds % 3600) / 60);
    
    if (hours > 0) {
        return `${hours} ч. ${minutes > 0 ? minutes + ' мин.' : ''}`;
    }
    return `${minutes} мин.`;
};

const ScheduleGeneratorPage = () => {
    const { scenarioId } = useParams();
    const navigate = useNavigate();
    const sId = Number(scenarioId);

    const [scenario, setScenario] = useState<any>(null);
    const [maxTime, setMaxTime] = useState(1800); // По умолчанию 30 минут (1800 сек)
    const [isGenerating, setIsGenerating] = useState(true);
    const [progress, setProgress] = useState(68);
    const [statusText, setStatusText] = useState("Оптимизация окон преподавателей...");

    const pollingRef = useRef<ReturnType<typeof setInterval> | null>(null);

    // 1. Инициализация и проверка: не идет ли уже генерация?
    useEffect(() => {
        const init = async () => {
            const sc = await dbService.get("scenarios", sId);
            setScenario(sc);
            
            // Запрашиваем статус сразу при загрузке
            const currentStatus = await scheduleDraftService.getStatus(sId);
            if (currentStatus.status === 1) { // 1 - ИДЕТ РАСЧЕТ
                setIsGenerating(true);
                startPolling();
            }
        };
        init();
        return () => stopPolling();
    }, [sId]);

    const stopPolling = () => {
        if (pollingRef.current) {
            clearInterval(pollingRef.current);
            pollingRef.current = null;
        }
    };

    const startPolling = () => {
        stopPolling(); // На всякий случай сбрасываем старый
        pollingRef.current = setInterval(async () => {
            try {
                const data = await scheduleDraftService.getStatus(sId);
                setProgress(data.progress);
                setStatusText(data.status_message);

                if (data.status === 2) { // ГОТОВО
                    stopPolling();
                    setIsGenerating(false);
                    navigate(`/ScheduleEditor/${sId}`);
                }
            } catch (e) {
                console.error("Потеряна связь с сервером...");
            }
        }, 3000); // Опрашиваем раз в 3 секунды (для долгих процессов чаще не нужно)
    };

    const handleStart = async () => {
        try {
            setIsGenerating(true);
            setProgress(0);
            setStatusText("Запуск алгоритма...");
            await scheduleDraftService.startGeneration(sId, maxTime);
            startPolling();
        } catch (err) {
            setIsGenerating(false);
            setStatusText("Ошибка старта");
        }
    };

    return (
        <div className="flex-col bg-main min-h-screen">
            <nav className="navbar">
                <div className="logo-white" onClick={() => navigate("/")} style={{cursor: 'pointer'}}>КГУ • ГЕНЕРАТОР</div>
                <button className="btn nav-btn" onClick={() => navigate(`/ScheduleEditor/${sId}`)}>Назад</button>
            </nav>

            <div className="flex-col align-center justify-center flex-grow p-4">
                <div className="card slide-up" style={{ width: '100%', maxWidth: '600px' }}>
                    <div className="flex-col gap-3">
                        <div className="text-center">
                            <h2 className="text-primary">Мастер генерации</h2>
                            <p className="text-muted">Сценарий: {scenario?.name}</p>
                        </div>

                        {!isGenerating ? (
                            <div className="flex-col gap-3 mt-2">
                                <div className="flex-col p-3 bg-main rounded-md" style={{border: '1px solid var(--border-color)'}}>
                                    <label className="filter-label">Максимальное время работы</label>
                                    <input 
                                        type="range" 
                                        min="600"    // 10 минут
                                        max="14400"  // 4 часа
                                        step="300"   // Шаг 5 минут
                                        className="w-100 mt-2"
                                        value={maxTime}
                                        onChange={(e) => setMaxTime(Number(e.target.value))}
                                    />
                                    <div className="flex-row space-between mt-1">
                                        <small className="text-muted">Мин: 10 мин</small>
                                        <div className="flex-col align-center">
                                            <strong className="text-primary" style={{fontSize: '1.4rem'}}>
                                                {formatSeconds(maxTime)}
                                            </strong>
                                        </div>
                                        <small className="text-muted">Макс: 4 часа</small>
                                    </div>
                                </div>

                                <div className="flex-col gap-1">
                                    <p style={{fontSize: '13px', color: '#666'}}>
                                        * Алгоритм будет перебирать миллионы комбинаций, стремясь минимизировать штрафные баллы (окна, перегрузки, смены корпусов).
                                    </p>
                                    <button className="btn btn-primary w-100 p-3 mt-1" onClick={handleStart} style={{fontSize: '1.1rem'}}>
                                        Начать глубокую оптимизацию
                                    </button>
                                </div>
                            </div>
                        ) : (
                            <div className="flex-col gap-3 mt-2 p-2">
                                <div className="flex-col gap-1">
                                    <div className="flex-row space-between">
                                        <span className="text-primary font-bold">Прогресс расчета</span>
                                        <span className="text-primary">{progress}%</span>
                                    </div>
                                    <div className="progress-bg" style={{ height: '24px', background: '#e0e4f0', borderRadius: '12px', overflow: 'hidden' }}>
                                        <div 
                                            className="progress-fill" 
                                            style={{ 
                                                width: `${progress}%`, 
                                                height: '100%', 
                                                backgroundColor: 'var(--p-green)',
                                                backgroundImage: 'linear-gradient(45deg, rgba(255,255,255,.15) 25%, transparent 25%, transparent 50%, rgba(255,255,255,.15) 50%, rgba(255,255,255,.15) 75%, transparent 75%, transparent)',
                                                backgroundSize: '40px 40px',
                                                transition: 'width 1s linear'
                                            }} 
                                        />
                                    </div>
                                </div>
                                
                                <div className="card bg-main p-3 text-center border-none">
                                    <div className="status-pulse mb-1"></div>
                                    <p className="font-bold">{statusText}</p>
                                    <p className="text-muted" style={{fontSize: '12px', marginTop: '10px'}}>
                                        Вы можете закрыть страницу. Процесс продолжится на сервере.
                                    </p>
                                </div>

                                <button className="btn btn-outline btn-red w-100" onClick={() => {
                                    if(window.confirm("Остановить генератор? Текущий результат не будет сохранен.")) {
                                        stopPolling();
                                        setIsGenerating(false);
                                    }
                                }}>
                                    Прервать процесс
                                </button>
                            </div>
                        )}
                    </div>
                </div>
            </div>
        </div>
    );
};

export default ScheduleGeneratorPage;