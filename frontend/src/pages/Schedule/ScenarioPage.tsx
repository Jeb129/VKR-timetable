import React, { useEffect, useState, useCallback } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { dbService } from '@/services/crud';
import { 
    type Scenario, 
    type Constraint, 
    type GenerationStatusResponse, 
    type PlannedCheckResult, 
    GenerationStatus 
} from '@/types/schedule';
import { semesterService, scenarioService } from '@/services/scenarioService';
import { useModal } from '@/context/ModalContext'; // Импортируем модалки
import ConstraintItem from '@/components/ConstraintItem';
import "@/styles/ScenarioDetail.css";

const ScenarioPage: React.FC = () => {
    const { id } = useParams<{ id: string }>();
    const scenarioId = Number(id);
    const navigate = useNavigate();
    const { openModal, closeModal } = useModal();

    const [scenario, setScenario] = useState<Scenario | null>(null);
    const [constraints, setConstraints] = useState<Constraint[]>([]);
    const [checkResult, setCheckResult] = useState<PlannedCheckResult | null>(null);
    const [genStatus, setGenStatus] = useState<GenerationStatusResponse | null>(null);
    const [polling, setPolling] = useState(false);
    const [error, setError] = useState<string | null>(null);

    // 1. Загрузка данных
    const fetchData = useCallback(async () => {
        try {
            const sData = await dbService.get<Scenario>('scenarios', scenarioId);
            setScenario(sData);

            const cData = await dbService.list<Constraint>('constraints', { page_size: 100 });
            setConstraints(cData.results);

            const check = await semesterService.checkPlanned(sData.semester);
            setCheckResult(check);

            if (sData.generation_status === GenerationStatus.IN_PROGRESS) {
                setPolling(true);
            }
        } catch (e) {
            setError("Не удалось загрузить данные сценария");
        }
    }, [scenarioId]);

    useEffect(() => { fetchData(); }, [fetchData]);

    // 2. Поллинг статуса генерации
    useEffect(() => {
        let interval: ReturnType<typeof setInterval> | null = null;
        if (polling) {
            const tick = async () => {
                try {
                    const status = await scenarioService.getGenStatus(scenarioId);
                    setGenStatus(status);
                    const isFinished = ['SUCCESS', 'FAILURE', 'REVOKED'].includes(status.celery_state || '');
                    if (isFinished || status.state === 'IDLE') {
                        setPolling(false);
                        fetchData();
                    }
                } catch (e) {
                    setPolling(false);
                }
            };
            tick(); 
            interval = setInterval(tick, 3000);
        }
        return () => { if (interval) clearInterval(interval); };
    }, [polling, scenarioId, fetchData]);

    // 3. Обработчики действий (замена алертов на модалки)
    const handleStart = async () => {
        try {
            const config = {
                time_limit: 300,
                num_workers: 4,
                constraints: constraints.map(c => ({ 
                    name: c.name, 
                    weight: c.weight, 
                    is_active: c.is_active 
                }))
            };
            await scenarioService.startGeneration(scenarioId, config);
            setPolling(true);
        } catch (e) {
            openModal({
                title: "Ошибка",
                content: <p>Не удалось запустить генерацию. Проверьте соединение с сервером.</p>
            });
        }
    };

    const handleSync = () => {
        openModal({
            title: "Подтверждение синхронизации",
            content: <p>Это действие удалит текущие плановые занятия семестра и создаст их заново на основе учебного плана. Продолжить?</p>,
            footer: (
                <div className="flex-row gap-2 w-100">
                    <button className="btn btn-red f-1" onClick={async () => {
                        if (scenario) {
                            await semesterService.syncPlanned(scenario.semester);
                            closeModal();
                            fetchData();
                        }
                    }}>Да, синхронизировать</button>
                    <button className="btn btn-outline f-1" onClick={closeModal}>Отмена</button>
                </div>
            )
        });
    };

    const handleStop = () => {
        openModal({
            title: "Остановка генерации",
            content: <p>Вы уверены, что хотите прервать процесс расчета расписания?</p>,
            footer: (
                <div className="flex-row gap-2 w-100">
                    <button className="btn btn-red f-1" onClick={async () => {
                        await scenarioService.stopGeneration(scenarioId);
                        closeModal();
                    }}>Остановить</button>
                    <button className="btn btn-outline f-1" onClick={closeModal}>Назад</button>
                </div>
            )
        });
    };

    const updateConstraint = (cId: number, data: Partial<Constraint>) => {
        setConstraints(prev => prev.map(c => c.id === cId ? { ...c, ...data } : c));
    };

    return (
        <div className="flex-col bg-main min-h-screen">
            <nav className="navbar">
                <div className="logo-white" onClick={() => navigate("/")} style={{cursor:'pointer'}}>КГУ • УПРАВЛЕНИЕ</div>
                <button className="btn nav-btn" onClick={() => navigate('/scenarios')}>К списку версий</button>
            </nav>

            <div className="profile-wrapper flex-col gap-3 w-100">
                {/* Header Card */}
                <div className="card flex-row space-between align-center slide-up w-100">
                    <div className="flex-col gap-1">
                        <h2 className="text-primary">{scenario?.name || "Загрузка..."}</h2>
                        <div className="flex-row gap-2 align-center">
                            <span className="badge btn-outline">ID: {scenarioId}</span>
                            <StatusBadge status={scenario?.generation_status} />
                        </div>
                    </div>
                    <div className="flex-row gap-2">
                        <button className="btn btn-primary" onClick={() => navigate(`/scenarios/${scenarioId}/edit`)}>
                            Ручное редактирование сетки
                        </button>
                        <button className="btn btn-orange" onClick={() => scenarioService.setActive(scenarioId)}>
                            Сделать основным
                        </button>
                    </div>
                </div>

                {error && <div className="error">{error}</div>}

                <div className="flex-row gap-3 align-start">
                    <div className="flex-col f-2 gap-3">
                        {/* Нагрузка */}
                        <div className="card flex-col gap-2">
                            <div className="flex-row space-between align-center">
                                <h3>Подготовка нагрузки</h3>
                                {checkResult?.status === 'ok' ? 
                                    <span className="text-green font-bold">Готово</span> : 
                                    <span className="text-orange font-bold">Внимание</span>
                                }
                            </div>
                            <div className="p-2 bg-main radius-md border-dashed">
                                {checkResult?.status === 'ok' ? 
                                    "Вся нагрузка семестра успешно распределена." : 
                                    `Не распределено: ${checkResult?.uncovered_data?.length || 0} записей.`
                                }
                            </div>
                            <button className="btn btn-outline w-100" onClick={handleSync}>
                                Синхронизировать с учебным планом
                            </button>
                        </div>

                        {/* Генератор */}
                        <div className="card flex-col gap-2">
                            <h3>Генератор расписания</h3>
                            <div className="p-3 bg-main radius-lg border-blue">
                                {polling ? (
                                    <div className="flex-col gap-2 align-center">
                                        <div className="spinner"></div>
                                        <strong className="text-orange">Выполняется расчет...</strong>
                                        <button className="btn btn-red w-100 mt-1" onClick={handleStop}>Остановить</button>
                                    </div>
                                ) : (
                                    <div className="flex-col gap-2">
                                        {scenario?.total_penalty !== undefined && (
                                            <div className="flex-row space-between border-bottom pb-1 mb-1">
                                                <span>Последний штраф:</span>
                                                <strong className="text-primary">{scenario.total_penalty}</strong>
                                            </div>
                                        )}
                                        <button className="btn btn-green w-100 py-2" onClick={handleStart}>
                                            Запустить автоматическую генерацию
                                        </button>
                                    </div>
                                )}
                            </div>
                        </div>
                    </div>

                    {/* Правая панель ограничений */}
                    <div className="flex-col f-1 card no-scroll sticky-top">
                        <h3 className="mb-2">Веса ограничений</h3>
                        <div className="scroll-y pr-1" style={{ maxHeight: '60vh' }}>
                            {constraints.map(c => (
                                <ConstraintItem key={c.id} constraint={c} onUpdate={updateConstraint} />
                            ))}
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
};

// Вспомогательный компонент статуса
const StatusBadge: React.FC<{ status?: GenerationStatus | null }> = ({ status }) => {
    const map = {
        [GenerationStatus.SUCCESS]: { label: 'Готово', cls: 'btn-green' },
        [GenerationStatus.IN_PROGRESS]: { label: 'Расчет', cls: 'btn-primary' },
        [GenerationStatus.ERROR]: { label: 'Ошибка', cls: 'btn-red' },
        [GenerationStatus.INFEASIBLE]: { label: 'Нерешаемо', cls: 'btn-orange' },
    };
    const item = (status !== undefined && status !== null) ? map[status] : { label: 'Новый', cls: 'btn-outline' };
    return <span className={`badge ${item?.cls || 'btn-outline'}`}>{item?.label || '---'}</span>;
};

export default ScenarioPage;