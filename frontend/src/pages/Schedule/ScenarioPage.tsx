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
import { useModal } from '@/context/ModalContext';
import ConstraintItem from '@/components/ConstraintItem';
import StatusBadge from '@/components/StatusBadge';
import "@/styles/ScenarioDetail.css";

const ScenarioPage: React.FC = () => {
    const { id } = useParams<{ id: string }>();
    const scenarioId = Number(id);
    const navigate = useNavigate();
    const { openModal, closeModal } = useModal();

    // Состояния данных
    const [scenario, setScenario] = useState<Scenario | null>(null);
    const [constraints, setConstraints] = useState<Constraint[]>([]);
    const [checkResult, setCheckResult] = useState<PlannedCheckResult | null>(null);
    const [genStatus, setGenStatus] = useState<GenerationStatusResponse | null>(null);
    
    // UI состояния
    const [polling, setPolling] = useState(false);
    const [formError, setFormError] = useState<string | null>(null);
    const [showUncoveredDetails, setShowUncoveredDetails] = useState(false);

    // Вспомогательная функция для обработки ошибок API
    const handleError = (e: any) => {
        const message = e.response?.data?.detail || e.response?.data?.error || "Произошла ошибка при выполнении операции";
        setFormError(message);
    };

    // 1. Загрузка данных
    const fetchData = useCallback(async () => {
        try {
            const sData = await dbService.get<Scenario>('scenarios', scenarioId);
            setScenario(sData);

            const cData = await dbService.list<Constraint>('constraints', { page_size: 100 });
            setConstraints(cData.results);

            const check = await semesterService.checkPlanned(sData.semester.id);
            setCheckResult(check);

            // Проверка: нужно ли запускать поллинг
            const currentStatus = sData.generation_status?.id;
            if (currentStatus === GenerationStatus.IN_PROGRESS || currentStatus === GenerationStatus.IN_QUERRY) {
                setPolling(true);
            }
        } catch (e) {
            setFormError("Не удалось загрузить данные сценария");
        }
    }, [scenarioId]);

    useEffect(() => { fetchData(); }, [fetchData]);

    // 2. Логика поллинга
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
                    // Если ошибка 404 (задача исчезла) - прекращаем опрос
                    setPolling(false);
                }
            };
            tick();
            interval = setInterval(tick, 3000);
        }
        return () => { if (interval) clearInterval(interval); };
    }, [polling, scenarioId, fetchData]);

    // 3. Действия
    const handleStart = async () => {
        setFormError(null);
        try {
            const config = {
                time_limit: 3600,
                num_workers: 4,
                constraints: constraints.map(c => ({
                    name: c.name,
                    weight: c.weight,
                    is_active: c.is_active
                }))
            };
            const sc = await scenarioService.startGeneration(scenarioId, config);
            if (sc) setScenario(sc);
            setPolling(true);
        } catch (e) {
            handleError(e);
        }
    };

    const handleSync = () => {
        let forceValue = false;
        openModal({
            title: "Синхронизация нагрузки",
            content: (
                <div className="flex-col gap-2">
                    <p>Это действие создаст плановые занятия на основе текущей нагрузки. Существующие записи будут удалены.</p>
                    <label className="flex-row align-center gap-1 pointer p-1 bg-main radius-md">
                        <input type="checkbox" onChange={(e) => forceValue = e.target.checked} />
                        <span className="font-bold text-red small">Игнорировать блокировки (Force)</span>
                    </label>
                </div>
            ),
            footer: (
                <div className="flex-row gap-2 w-100">
                    <button className="btn btn-red f-1" onClick={async () => {
                        try {
                            if (scenario) {
                                await semesterService.syncPlanned(scenario.semester.id, forceValue);
                                closeModal();
                                fetchData();
                            }
                        } catch (e) {
                            handleError(e);
                            closeModal();
                        }
                    }}>Выполнить</button>
                    <button className="btn btn-outline f-1" onClick={closeModal}>Отмена</button>
                </div>
            )
        });
    };

    const handleActivate = () => {
        let forceValue = false;
        openModal({
            title: "Активация сценария",
            content: (
                <div className="flex-col gap-2">
                    <p>Сделать этот сценарий основным для отображения в общем расписании?</p>
                    <label className="flex-row align-center gap-1 pointer p-1 bg-main radius-md">
                        <input type="checkbox" onChange={(e) => forceValue = e.target.checked} />
                        <span className="font-bold text-orange small">Принудительно переназначить</span>
                    </label>
                </div>
            ),
            footer: (
                <div className="flex-row gap-2 w-100">
                    <button className="btn btn-green f-1" onClick={async () => {
                        try {
                            await scenarioService.setActive(scenarioId, forceValue);
                            closeModal();
                            fetchData();
                        } catch (e) {
                            handleError(e);
                            closeModal();
                        }
                    }}>Активировать</button>
                    <button className="btn btn-outline f-1" onClick={closeModal}>Отмена</button>
                </div>
            )
        });
    };

    const updateConstraint = (cId: number, data: Partial<Constraint>) => {
        setConstraints(prev => prev.map(c => c.id === cId ? { ...c, ...data } : c));
    };

    // Проверка, занят ли сейчас генератор
    const isBusy = polling || scenario?.generation_status?.id === GenerationStatus.IN_PROGRESS || scenario?.generation_status?.id === GenerationStatus.IN_QUERRY;

    return (
        <div className="flex-col min-h-screen">
            <nav className="navbar">
                <div className="logo-white pointer" onClick={() => navigate("/")}>КГУ • УПРАВЛЕНИЕ</div>
                <button className="btn nav-btn" onClick={() => navigate('/scenarios')}>К списку версий</button>
            </nav>

            <div className="p-3 flex-col gap-3">
                {/* Ошибки формы */}
                {formError && (
                    <div className="error-box slide-up" onClick={() => setFormError(null)}>
                        <strong>⚠ Ошибка:</strong> {formError}
                        <div className="small mt-1">(Нажмите, чтобы скрыть)</div>
                    </div>
                )}

                {/* Шапка сценария */}
                <div className="card flex-row space-between align-center slide-up flex-wrap gap-2">
                    <div className="flex-col gap-1">
                        <h2 className="text-primary m-0">{scenario?.name || "Загрузка..."}</h2>
                        <div className="flex-row gap-2 align-center">
                            <span className="badge btn-outline">ID: {scenarioId}</span>
                            <StatusBadge status={scenario?.generation_status} />
                            {scenario?.semester.name && <span className="text-muted">| {scenario.semester.name}</span>}
                        </div>
                    </div>
                    <div className="flex-row gap-2">
                        <button className="btn btn-primary" onClick={() => navigate(`/scenarios/${scenarioId}/edit`)}>
                            📅 Редактор сетки
                        </button>
                        <button className="btn btn-orange" onClick={handleActivate}>
                            ⭐ Сделать основным
                        </button>
                    </div>
                </div>

                {/* Основная сетка */}
                <div className="layout-grid align-stretch">
                    
                    {/* Левая колонка */}
                    <div className="flex-col f-2 gap-3 w-100">

                        {/* Блок нагрузки */}
                        <div className="card flex-col gap-2">
                            <div className="flex-row space-between align-center">
                                <h3 className="m-0">Подготовка данных</h3>
                                {checkResult?.status === 'ok' ?
                                    <span className="badge btn-green">Готово</span> :
                                    <span className="badge btn-red">Требуется проверка</span>
                                }
                            </div>

                            <div className="p-3 bg-main radius-md border-dashed">
                                {checkResult?.status === 'ok' ? (
                                    <p className="text-green text-center m-0 font-bold">✓ Все часы учебного плана распределены.</p>
                                ) : (
                                    <div className="flex-col gap-2">
                                        <div className="flex-row space-between align-center">
                                            <p className="text-red m-0 font-bold">
                                                Не распределено: {checkResult?.uncovered_data?.length || 0} поз.
                                            </p>
                                            <button
                                                className="btn btn-outline nav-btn"
                                                style={{ color: 'var(--p-blue)' }}
                                                onClick={() => setShowUncoveredDetails(!showUncoveredDetails)}
                                            >
                                                {showUncoveredDetails ? "Скрыть" : "Детали"}
                                            </button>
                                        </div>

                                        {showUncoveredDetails && (
                                            <div className="mt-1 scroll-y" style={{ maxHeight: '200px' }}>
                                                <table className="mini-table w-100">
                                                    <thead>
                                                        <tr>
                                                            <th>Дисциплина / Группа</th>
                                                            <th className="text-center">Часы</th>
                                                        </tr>
                                                    </thead>
                                                    <tbody>
                                                        {checkResult?.uncovered_data?.map((item: any, idx: number) => (
                                                            <tr key={idx}>
                                                                <td>
                                                                    <div className="font-bold">{item.discipline_name}</div>
                                                                    <div className="small text-muted">{item.group_name}</div>
                                                                </td>
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
                                🔄 Синхронизировать нагрузку
                            </button>
                        </div>

                        {/* Блок управления генерацией */}
                        <div className="card flex-col gap-2">
                            <h3 className="m-0">Управление расчетом</h3>
                            <div className="p-4 bg-main radius-lg border-blue">
                                {isBusy ? (
                                    <div className="flex-col gap-3 align-center py-2">
                                        <div className="spinner"></div>
                                        <div className="flex-col align-center">
                                            <strong className="text-orange" style={{ fontSize: '1.1rem' }}>
                                                {genStatus?.celery_state === 'PENDING' ? 'В очереди...' : 'Выполняется расчет...'}
                                            </strong>
                                            <span className="text-muted small mt-1">ID задачи: {genStatus?.task_id?.substring(0, 12)}...</span>
                                        </div>
                                        
                                        <div className="log-container">
                                            <div>[SYSTEM] Connection: OK</div>
                                            <div>[CELERY] State: {genStatus?.celery_state}</div>
                                            {genStatus?.start_time && <div>[TIME] Started: {new Date(genStatus.start_time).toLocaleTimeString()}</div>}
                                            {genStatus?.stop_signal && <div className="text-red">[SIGNAL] Termination sent...</div>}
                                        </div>

                                        <button className="btn btn-red w-100" onClick={() => scenarioService.stopGeneration(scenarioId).then(() => fetchData())}>
                                            Остановить расчет
                                        </button>
                                    </div>
                                ) : (
                                    <div className="flex-col gap-3">
                                        <div className="flex-row space-between align-center">
                                            <span className="text-muted small">Результат:</span>
                                            <div className="flex-row align-center gap-1">
                                                {scenario?.total_penalty !== undefined && (
                                                    <span className="badge btn-outline">Штраф: {scenario.total_penalty}</span>
                                                )}
                                                <StatusBadge status={scenario?.generation_status} />
                                            </div>
                                        </div>
                                        
                                        <button
                                            className="btn btn-green w-100 py-3 font-bold"
                                            style={{ fontSize: '1.1rem' }}
                                            onClick={handleStart}
                                            disabled={checkResult?.status !== 'ok'}
                                        >
                                            🚀 Запустить генерацию
                                        </button>
                                        
                                        {checkResult?.status !== 'ok' && (
                                            <p className="text-red text-center small m-0">
                                                * Запуск невозможен: есть нераспределенная нагрузка.
                                            </p>
                                        )}
                                    </div>
                                )}
                            </div>
                        </div>
                    </div>

                    {/* Правая колонка: Ограничения */}
                    <div className="flex-col f-1 card w-100">
                        <div className="flex-row space-between align-center mb-2">
                            <h3 className="m-0">Конфигурация ограничений</h3>
                            <span className="badge btn-primary">{constraints.length}</span>
                        </div>
                        <div className="scroll-y pr-1 max-h-35">
                            <div className="flex-col gap-1">
                                {constraints.map(c => (
                                    <ConstraintItem key={c.id} constraint={c} onUpdate={updateConstraint} />
                                ))}
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default ScenarioPage;