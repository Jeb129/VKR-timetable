import React, { useEffect, useState, useCallback } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { dbService } from '@/services/crud';
import { 
    type Scenario, 
    type Constraint, 
    type GenerationStatusResponse, 
    GenerationStatus 
} from '@/types/schedule';
import { type PlannedCheckResult } from '@/types/plannedlessons';
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

    const [showUncoveredDetails, setShowUncoveredDetails] = useState(false);

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
                <div className="card flex-row space-between align-center slide-up w-100">
                    <div className="flex-col gap-1">
                        <h2 className="text-primary">{scenario?.name || "Загрузка..."}</h2>
                        <div className="flex-row gap-2 align-center">
                            <span className="badge btn-outline">ID: {scenarioId}</span>
                            <StatusBadge status={scenario?.generation_status} />
                            {scenario?.semester_name && <span className="text-muted">| {scenario.semester_name}</span>}
                        </div>
                    </div>
                    <div className="flex-row gap-2">
                        <button className="btn btn-primary" onClick={() => navigate(`/scenarios/${scenarioId}/edit`)}>
                            Редактор сетки
                        </button>
                        <button className="btn btn-orange" onClick={() => scenarioService.setActive(scenarioId)}>
                            Сделать основным
                        </button>
                    </div>
                </div>

                <div className="flex-row gap-3 align-start">
                    <div className="flex-col f-2 gap-3">
                        
                        <div className="card flex-col gap-2">
                            <div className="flex-row space-between align-center">
                                <h3>Подготовка нагрузки (Academic Load)</h3>
                                {checkResult?.status === 'ok' ? 
                                    <span className="badge btn-green">Покрыта полностью</span> : 
                                    <span className="badge btn-red">Есть пробелы</span>
                                }
                            </div>
                            
                            <div className="p-3 bg-main radius-md border-dashed">
                                {checkResult?.status === 'ok' ? (
                                    <p className="text-green text-center font-bold"> Все часы учебного плана распределены по занятиям.</p>
                                ) : (
                                    <div className="flex-col gap-2">
                                        <div className="flex-row space-between align-center">
                                            <p className="text-red m-0">
                                                Не распределено: <strong>{checkResult?.uncovered_data?.length || 0}</strong> позиций нагрузки.
                                            </p>
                                            <button 
                                                className="btn btn-outline" 
                                                style={{padding: '4px 12px', fontSize: '12px'}}
                                                onClick={() => setShowUncoveredDetails(!showUncoveredDetails)}
                                            >
                                                {showUncoveredDetails ? "Скрыть список" : "Показать список"}
                                            </button>
                                        </div>

                                        {showUncoveredDetails && (
                                            <div className="mt-2 scroll-y" style={{maxHeight: '250px'}}>
                                                <table className="mini-table w-100">
                                                    <thead>
                                                        <tr>
                                                            <th>Дисциплина</th>
                                                            <th>Группа</th>
                                                            <th className="text-center">Остаток</th>
                                                        </tr>
                                                    </thead>
                                                    <tbody>
                                                        {checkResult?.uncovered_data?.map((item: any, idx: number) => (
                                                            <tr key={idx}>
                                                                <td>{item.discipline_name}</td>
                                                                <td>{item.group_name}</td>
                                                                <td className="text-center text-red font-bold">{item.hours_uncovered} ч.</td>
                                                            </tr>
                                                        ))}
                                                    </tbody>
                                                </table>
                                            </div>
                                        )}
                                    </div>
                                )}
                            </div>
                            
                            <button className="btn btn-outline w-100" onClick={handleSync}>
                                Синхронизировать плановые занятия
                            </button>
                        </div>

                        <div className="card flex-col gap-2">
                            <h3>Автоматическая генерация</h3>
                            <div className="p-4 bg-main radius-lg border-blue">
                                {polling ? (
                                    <div className="flex-col gap-3 align-center py-2">
                                        <div className="spinner"></div>
                                        <div className="flex-col align-center">
                                            <strong className="text-orange" style={{fontSize: '1.2rem'}}>Идет расчет в Celery...</strong>
                                            <span className="text-muted small">Задача: {genStatus?.task_id?.substring(0,8)}...</span>
                                        </div>
                                        <button className="btn btn-red mt-2" onClick={handleStop}>Прервать расчет</button>
                                    </div>
                                ) : (
                                    <div className="flex-col gap-3">
                                        <div className="flex-row space-between align-center">
                                            <span className="text-muted">Результат последнего прогона:</span>
                                            <div className="flex-row align-center gap-2">
                                                {scenario?.total_penalty !== undefined && (
                                                    <span className="badge btn-outline">Штраф: {scenario.total_penalty}</span>
                                                )}
                                                <StatusBadge status={scenario?.generation_status} />
                                            </div>
                                        </div>
                                        <button 
                                            className="btn btn-green w-100 py-3 font-bold" 
                                            style={{fontSize: '1.1rem'}}
                                            onClick={handleStart}
                                            disabled={checkResult?.status !== 'ok'}
                                        >
                                            Запустить генератор
                                        </button>
                                        {checkResult?.status !== 'ok' && (
                                            <p className="text-red text-center small">* Нельзя запустить генератор, пока не распределена вся нагрузка</p>
                                        )}
                                    </div>
                                )}
                            </div>
                        </div>
                    </div>

                    <div className="flex-col f-1 card no-scroll sticky-top">
                        <div className="flex-row space-between align-center mb-2">
                            <h3>Веса ограничений</h3>
                            <span className="badge btn-primary">{constraints.length}</span>
                        </div>
                        <div className="scroll-y pr-1" style={{ maxHeight: 'calc(100vh - 350px)' }}>
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