import { useState, useEffect } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { dbService } from "@/services/crud";
import { scheduleDraftService } from "@/services/schedule_editor";
import "@/styles/Generator.css";

const ScheduleGeneratorPage = () => {
    const { scenarioId } = useParams();
    const navigate = useNavigate();
    const sId = Number(scenarioId);

    // Состояния
    const [scenario, setScenario] = useState<any>(null);
    const [plannedLessons, setPlannedLessons] = useState<any[]>([]);
    const [isGenerating, setIsGenerating] = useState(false);
    const [progress, setProgress] = useState(0);

    // Параметры алгоритма
    const [config, setConfig] = useState({
        iterations: 10000,
        coolingRate: 0.9995,
        t_start: 100.0
    });

    useEffect(() => {
        const loadInfo = async () => {
            const sc = await dbService.get("scenarios", sId);
            setScenario(sc);
            // Заглушка списка нагрузок
            const mockLoad = [
                { id: 1, discipline: "Высшая математика", group: "22-ИСбо-1", hours: 4, type: "Лекция" },
                { id: 2, discipline: "Базы данных", group: "23-ПИНбо-2", hours: 2, type: "Практика" },
                { id: 3, discipline: "Физика", group: "22-ИСбо-1", hours: 2, type: "Лекция" },
            ];
            setPlannedLessons(mockLoad);
        };
        loadInfo();
    }, [sId]);

    const handleStartGeneration = async () => {
        setIsGenerating(true);
        setProgress(10);

        // ИМИТАЦИЯ ПРОГРЕССА (пока нет вьюхи)
        const interval = setInterval(() => {
            setProgress(prev => {
                if (prev >= 90) {
                    clearInterval(interval);
                    return 95;
                }
                return prev + 5;
            });
        }, 800);

        try {
            // В будущем тут будет реальный вызов
            // await scheduleDraftService.startGeneration(sId, config);
            
            // Имитируем долгий расчет
            setTimeout(() => {
                clearInterval(interval);
                setIsGenerating(false);
                navigate(`/ScheduleEditor/${sId}`); // После генерации идем в редактор смотреть результат
            }, 5000);

        } catch (err) {
            setIsGenerating(false);
            clearInterval(interval);
            alert("Ошибка при запуске генератора");
        }
    };

    return (
        <div className="flex-col bg-main min-h-screen">
            <nav className="navbar">
                <div className="logo-white" onClick={() => navigate("/")}>КГУ • ГЕНЕРАТОР</div>
                <button className="btn nav-btn" onClick={() => navigate(`/ScheduleEditor/${sId}`)}>Назад в редактор</button>
            </nav>

            <div className="profile-wrapper flex-col gap-3">
                <div className="flex-row space-between align-end">
                    <div>
                        <h2 className="text-primary">Автоматическая генерация</h2>
                        <p className="text-muted">Версия: <b>{scenario?.name}</b></p>
                    </div>
                </div>

                <div className="settings-grid">
                    {/* НАСТРОЙКИ */}
                    <div className="card flex-col gap-2">
                        <h3>Параметры алгоритма</h3>
                        <div className="flex-col">
                            <label className="filter-label">Количество итераций</label>
                            <input 
                                type="number" className="input-styled" 
                                value={config.iterations} 
                                onChange={e => setConfig({...config, iterations: Number(e.target.value)})}
                                disabled={isGenerating}
                            />
                            <small className="text-muted">Больше итераций — выше качество, но дольше расчет.</small>
                        </div>

                        <div className="flex-col">
                            <label className="filter-label">Коэффициент охлаждения</label>
                            <input 
                                type="number" step="0.0001" className="input-styled" 
                                value={config.coolingRate}
                                onChange={e => setConfig({...config, coolingRate: Number(e.target.value)})}
                                disabled={isGenerating}
                            />
                        </div>

                        {!isGenerating ? (
                            <button className="btn btn-primary mt-2" onClick={handleStartGeneration}>
                                Запустить расчет расписания
                            </button>
                        ) : (
                            <div className="flex-col gap-1 mt-2">
                                <div className="progress-pulse"></div>
                                <p className="text-center text-primary font-bold">Идет подбор оптимальных слотов: {progress}%</p>
                            </div>
                        )}
                    </div>

                    {/* СПИСОК ЗАДАЧ */}
                    <div className="card flex-col">
                        <h3>Учебный план (Задачи)</h3>
                        <p className="text-muted mb-1" style={{fontSize: '0.8rem'}}>Будет создано {plannedLessons.length} занятий</p>
                        <div className="load-list">
                            {plannedLessons.map(item => (
                                <div key={item.id} className="load-item flex-row space-between">
                                    <div className="flex-col">
                                        <strong>{item.discipline}</strong>
                                        <span>{item.group}</span>
                                    </div>
                                    <div className="text-right">
                                        <span className="badge btn-outline">{item.type}</span>
                                        <div className="mt-1">{item.hours} ч.</div>
                                    </div>
                                </div>
                            ))}
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default ScheduleGeneratorPage;