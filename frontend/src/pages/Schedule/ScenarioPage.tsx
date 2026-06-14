import React, { useEffect, useState, useCallback } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { dbService } from '@/services/crud';
import { type Scenario, type Constraint, type GenerationStatusResponse, type PlannedCheckResult, GenerationStatus } from '@/types/schedule';
import "@/styles/ScenarioDetail.css";
import { semesterService, scenarioService } from '@/services/scenarioService';
import ConstraintItem from '@/components/ConstraintItem';


const ScenarioPage: React.FC = () => {
    const { id } = useParams<{ id: string }>();
    const scenarioId = Number(id);
    const navigate = useNavigate();

    const [scenario, setScenario] = useState<Scenario | null>(null);
    const [constraints, setConstraints] = useState<Constraint[]>([]);
    const [checkResult, setCheckResult] = useState<PlannedCheckResult | null>(null);
    const [genStatus, setGenStatus] = useState<GenerationStatusResponse | null>(null);
    const [polling, setPolling] = useState(false);

    // 1. Загрузка данных
    const fetchData = useCallback(async () => {
        try {
            const sData = await dbService.get<Scenario>('scenarios', scenarioId);
            console.log(sData)
            setScenario(sData);

            const cData = await dbService.list<Constraint>('constraints', { page_size: 100 });
            setConstraints(cData.results);

            const check = await semesterService.checkPlanned(sData.semester);
            setCheckResult(check);

            // Если статус уже в процессе - включаем поллинг сразу
            if (sData.generation_status === GenerationStatus.IN_PROGRESS) {
                setPolling(true);
            }
        } catch (e) {
            console.error("Ошибка при загрузке данных сценария:", e);
        }
    }, [scenarioId]);

    useEffect(() => { fetchData(); }, [fetchData]);

    // 2. Поллинг (Исправленный)
    useEffect(() => {
        let interval: ReturnType<typeof setInterval> | null = null;

        if (polling) {
            console.log("Запуск поллинга для сценария:", scenarioId);
            // Сразу делаем первый запрос, не дожидаясь 3 секунд
            const tick = async () => {
                try {
                    const status = await scenarioService.getGenStatus(scenarioId);
                    setGenStatus(status);
                    
                    // Условие остановки: задача в Celery завершена (SUCCESS / FAILURE / REVOKED)
                    const isFinished = ['SUCCESS', 'FAILURE', 'REVOKED'].includes(status.celery_state || '');
                    
                    if (isFinished || status.state === 'IDLE') {
                        console.log("Поллинг завершен, статус:", status.celery_state);
                        setPolling(false);
                        fetchData(); // Обновляем данные сценария (статус в БД)
                    }
                } catch (e) {
                    console.error("Ошибка поллинга:", e);
                    setPolling(false);
                }
            };

            tick(); 
            interval = setInterval(tick, 3000);
        }

        return () => {
            if (interval) {
                console.log("Остановка поллинга");
                clearInterval(interval);
            }
        };
    }, [polling, scenarioId, fetchData]);

    // 3. Обработчики
    const updateConstraint = (cId: number, data: Partial<Constraint>) => {
        setConstraints(prev => prev.map(c => c.id === cId ? { ...c, ...data } : c));
    };

    const handleStart = async () => {
        try {
            const config = {
                time_limit: 300,
                num_workers: 4,
                // Передаем актуальные веса из нашего стейта
                constraints: constraints.map(c => ({ 
                    name: c.name, 
                    weight: c.weight, 
                    is_active: c.is_active 
                }))
            };
            await scenarioService.startGeneration(scenarioId, config);
            setPolling(true);
        } catch (e) {
            alert("Не удалось запустить генерацию");
        }
    };
    const handleSync = async () => {
        if (!window.confirm("Это удалит текущие плановые занятия семестра! Продолжить?")) return;
        if (scenario) {
            await semesterService.syncPlanned(scenario.semester);
            fetchData();
        }
    };
    const handleStop = async () => {
        if (window.confirm("Остановить процесс генерации?")) {
            await scenarioService.stopGeneration(scenarioId);
            // Мы не выключаем polling здесь, дождемся пока бэк подтвердит REVOKED
        }
    };

    return (
        <div className="flex-col p-3 gap-3">
            {/* Header */}
            <div className="card flex-row space-between align-center">
                <div className="flex-col">
                    <h2 className="text-primary">{scenario?.name || "Загрузка..."}</h2>
                    <div className="flex-row gap-2 align-center mt-1">
                        <span className="badge btn-outline">ID: {scenarioId}</span>
                        <StatusBadge status={scenario?.generation_status} />
                    </div>
                </div>
                <div className="flex-row gap-2">
                    {/* КНОПКА ПЕРЕХОДА В РЕДАКТОР */}
                    <button 
                        className="btn btn-primary" 
                        onClick={() => navigate(`/scenarios/${scenarioId}/edit`)}
                    >
                        📅 Редактор сетки
                    </button>
                    <button className="btn btn-orange nav-btn" onClick={() => scenarioService.setActive(scenarioId)}>Сделать основным</button>
                    <button className="btn btn-outline" onClick={() => navigate('/scenarios')}>Назад</button>
                </div>
            </div>

            <div className="flex-row gap-3 align-start">
                <div className="flex-col f-2 gap-3">
                    
                    {/* Виджет нагрузки */}
                    <div className="card">
                        <div className="flex-row space-between align-center">
                            <h3>Подготовка нагрузки</h3>
                            {checkResult?.status === 'ok' ? 
                                <span className="text-green fw-bold">✓ Готово</span> : 
                                <span className="text-orange fw-bold">⚠ Требуется внимание</span>
                            }
                        </div>
                        <div className="p-2 mt-1 bg-main radius-md" style={{ border: '1px dashed var(--border-color)' }}>
                            {checkResult?.status === 'ok' ? (
                                <p className="text-green">Все часы учебного плана успешно распределены по плановым занятиям.</p>
                            ) : (
                                <p className="text-red">Обнаружено нераспределенной нагрузки: <strong>{checkResult?.uncovered_data?.length || 0}</strong> записей.</p>
                            )}
                        </div>
                        <button className="btn btn-outline w-100 mt-2" onClick={handleSync}>
                            🔄 Синхронизировать с учебным планом
                        </button>
                    </div>

                    {/* Мониторинг генерации */}
                    <div className="card">
                        <h3>Статус генератора</h3>
                        <div className="mt-2 p-3 bg-main radius-lg border-blue">
                            {polling ? (
                                <div className="flex-col gap-2">
                                    <div className="flex-row align-center gap-2">
                                        <div className="spinner"></div>
                                        <span className="text-primary fw-bold">Идет расчет расписания...</span>
                                    </div>
                                    <div className="log-container">
                                        <div>[Система] Задача: {genStatus?.task_id}</div>
                                        <div>[Статус] Celery: {genStatus?.celery_state}</div>
                                        <div>[Время] Старт: {genStatus?.start_time ? new Date(genStatus.start_time).toLocaleTimeString() : '---'}</div>
                                        {genStatus?.stop_signal && <div className="text-orange">(!) Получен сигнал на прерывание...</div>}
                                    </div>
                                    <button className="btn btn-red w-100" onClick={handleStop}>Остановить процесс</button>
                                </div>
                            ) : (
                                <div className="flex-col gap-3">
                                    <div className="flex-row space-between align-center">
                                        <span className="text-muted">Последний результат:</span>
                                        <StatusBadge status={scenario?.generation_status} />
                                    </div>
                                    {scenario?.total_penalty !== undefined && (
                                        <div className="flex-row space-between border-bottom pb-1">
                                            <span>Итоговый штраф:</span>
                                            <span className="fw-bold text-primary">{scenario.total_penalty}</span>
                                        </div>
                                    )}
                                    <button className="btn btn-green w-100 py-2" onClick={handleStart} style={{ fontSize: '1.1rem' }}>
                                        🚀 Запустить генерацию
                                    </button>
                                </div>
                            )}
                        </div>
                    </div>
                </div>

                {/* Правая панель: Интерактивные ограничения */}
                <div className="flex-col f-1 card no-scroll" style={{ position: 'sticky', top: '1rem' }}>
                    <div className="flex-row space-between align-center mb-2">
                        <h3>Параметры (Constraints)</h3>
                        <span className="badge btn-primary">{constraints.filter(c => c.is_active).length}</span>
                    </div>
                    <div className="scroll-y pr-1" style={{ maxHeight: 'calc(100vh - 250px)' }}>
                        {constraints.length > 0 ? (
                            constraints.map(c => (
                                <ConstraintItem 
                                    key={c.id} 
                                    constraint={c} 
                                    onUpdate={updateConstraint} 
                                />
                            ))
                        ) : (
                            <p className="text-muted p-2">Загрузка правил...</p>
                        )}
                    </div>
                    <div className="mt-2 pt-2 border-top text-muted" style={{ fontSize: '0.75rem' }}>
                        * Веса влияют на приоритет мягких ограничений при поиске решения.
                    </div>
                </div>
            </div>
        </div>
    );
};
const ScenarioPage_old: React.FC = () => {
    const { id } = useParams<{ id: string }>();
    const scenarioId = Number(id);

    const [scenario, setScenario] = useState<Scenario | null>(null);
    const [constraints, setConstraints] = useState<Constraint[]>([]);
    const [checkResult, setCheckResult] = useState<PlannedCheckResult | null>(null);
    const [genStatus, setGenStatus] = useState<GenerationStatusResponse | null>(null);
    const [polling, setPolling] = useState(false);
    const navigate = useNavigate()

    // 1. Загрузка данных
    const fetchData = useCallback(async () => {
        const sData = await dbService.get<Scenario>('scenarios', scenarioId);
        setScenario(sData);
        
        const cData = await dbService.list<Constraint>('constraints', { page_size: 100 });
        setConstraints(cData.results);

        // Проверка нагрузки (нужен ID семестра из сценария)
        const check = await semesterService.checkPlanned(sData.semester);
        setCheckResult(check);

        if (sData.generation_status === GenerationStatus.IN_PROGRESS) {
            setPolling(true);
        }
    }, [scenarioId]);

    useEffect(() => { fetchData(); }, [fetchData]);

    // 2. Поллинг статуса генерации
    useEffect(() => {
        let interval: ReturnType<typeof setInterval>;
        if (polling) {
            interval = setInterval(async () => {
                const status = await scenarioService.getGenStatus(scenarioId);
                setGenStatus(status);
                // Если Celery закончил или статус в БД сменился (успех/ошибка)
                if (status.celery_state === 'SUCCESS' || status.celery_state === 'FAILURE') {
                    setPolling(false);
                    fetchData();
                }
            }, 3000);
        }
        return () => clearInterval(interval);
    }, [polling, scenarioId, fetchData]);

    // 3. Действия
    const handleSync = async () => {
        if (!window.confirm("Это удалит текущие плановые занятия семестра! Продолжить?")) return;
        if (scenario) {
            await semesterService.syncPlanned(scenario.semester);
            fetchData();
        }
    };

    const handleStart = async () => {
        const config = {
            time_limit: 300,
            num_workers: 4,
            constraints: constraints.map(c => ({ name: c.name, weight: c.weight, is_active: c.is_active }))
        };
        await scenarioService.startGeneration(scenarioId, config);
        setPolling(true);
    };

    return (
        <div className="flex-col p-3 gap-3">
            {/* Header */}
            <div className="card flex-row space-between align-center">
                <div className="flex-col">
                    <h2 className="text-primary">{scenario?.name}</h2>
                    <span className="text-muted">ID Сценария: {scenarioId}</span>
                </div>
                <div className="flex-row gap-2">
                    <button className="btn btn-orange" onClick={() => scenarioService.setActive(scenarioId)}>Сделать активным</button>
                    <button className="btn btn-outline" onClick={() => navigate('/scenarios')}>Назад</button>
                </div>
            </div>

            <div className="flex-row gap-3">
                {/* Левая панель: Нагрузка и Генерация */}
                <div className="flex-col f-2 gap-3">
                    
                    {/* Виджет проверки нагрузки */}
                    <div className="card">
                        <h3>Проверка нагрузки</h3>
                        {checkResult?.status === 'ok' ? (
                            <div className="p-2 mt-1 bg-green-light text-green radius-md">✓ Нагрузка полностью покрыта</div>
                        ) : (
                            <div className="p-2 mt-1 bg-red-light text-red radius-md">
                                ⚠ Не распределено записей нагрузки: {checkResult?.uncovered_data?.length}
                            </div>
                        )}
                        <button className="btn btn-primary mt-2" onClick={handleSync}>
                            Обновить плановые занятия
                        </button>
                    </div>

                    {/* Мониторинг генерации */}
                    <div className="card">
                        <h3>Генератор</h3>
                        <div className="mt-2">
                            {polling ? (
                                <div className="flex-col gap-2">
                                    <div className="status-indicator">
                                        <div className="spinner"></div>
                                        <span>Статус задачи: <strong>{genStatus?.celery_state}</strong></span>
                                    </div>
                                    <div className="log-container">
                                        {/* Здесь можно выводить логи из genStatus.logs если они есть */}
                                        <div>Задача запущена в {genStatus?.start_time}...</div>
                                        {genStatus?.stop_signal && <div className="text-red">Сигнал остановки получен...</div>}
                                    </div>
                                    <button className="btn btn-red" onClick={() => scenarioService.stopGeneration(scenarioId)}>
                                        Остановить расчет
                                    </button>
                                </div>
                            ) : (
                                <div className="flex-col gap-2">
                                    <div className="flex-row space-between align-center">
                                        <span>Последний результат:</span>
                                        <StatusBadge status={scenario?.generation_status} />
                                    </div>
                                    <button className="btn btn-green w-100" onClick={handleStart}>
                                        Запустить генерацию
                                    </button>
                                </div>
                            )}
                        </div>
                    </div>
                </div>

                {/* Правая панель: Настройки ограничений */}
                <div className="flex-col f-1 card">
                    <h3>Ограничения (Constraints)</h3>
                    <div className="scroll-y mt-2" style={{maxHeight: '500px'}}>
                        {constraints.map(c => (
                            <div key={c.id} className="constraint-row flex-col gap-1 p-1">
                                <div className="flex-row space-between">
                                    <span style={{fontSize: '0.9rem', fontWeight: 600}}>{c.description}</span>
                                    <input type="checkbox" checked={c.is_active} readOnly />
                                </div>
                                <div className="flex-row align-center gap-2">
                                    <input type="range" className="f-1" min="0" max="100" value={c.weight} readOnly />
                                    <span className="text-muted">{c.weight}</span>
                                </div>
                            </div>
                        ))}
                    </div>
                </div>
            </div>
        </div>
    );
};

const StatusBadge: React.FC<{ status?: GenerationStatus | null }> = ({ status }) => {
    const map = {
        [GenerationStatus.SUCCESS]: { label: 'Готово', cls: 'btn-green' },
        [GenerationStatus.IN_PROGRESS]: { label: 'В процессе', cls: 'btn-primary' },
        [GenerationStatus.ERROR]: { label: 'Ошибка', cls: 'btn-red' },
        [GenerationStatus.INFEASIBLE]: { label: 'Нерешаемо', cls: 'btn-orange' },
    };
    if (status === null || status === undefined) return <span className="badge btn-outline">Новый</span>;
    const item = map[status] || { label: 'Неизвестно', cls: 'btn-outline' };
    return <span className={`badge ${item.cls}`}>{item.label}</span>;
};

export default ScenarioPage;