import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { scenarioService } from "@/services/scenarioService";
import type { Scenario } from "@/types/schedule";
import "@/styles/ScenarioSelection.css";

const ScenarioSelectionPage = () => {
    const navigate = useNavigate();
    
    const [scenarios, setScenarios] = useState<Scenario[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    
    const [isCreating, setIsCreating] = useState(false);
    const [newName, setNewName] = useState("");

    const fetchScenarios = async () => {
        setLoading(true);
        setError(null);
        try {
            const data = await scenarioService.getAll();
            setScenarios(data);
        } catch (err) {
            setError("Ошибка загрузки списка сценариев");
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchScenarios();
    }, []);

    const handleCreate = async () => {
        if (!newName.trim()) return;
        try {
            await scenarioService.create(newName);
            setNewName("");
            setIsCreating(false);
            await fetchScenarios();
        } catch (err) {
            setError("Не удалось создать сценарий");
        }
    };

    const handleCopy = async (id: number) => {
        try {
            await scenarioService.copy(id);
            await fetchScenarios();
        } catch (err) {
            setError("Ошибка копирования");
        }
    };

    const handleDelete = async (id: number) => {
        try {
            await scenarioService.remove(id);
            await fetchScenarios();
        } catch (err) {
            setError("Ошибка удаления");
        }
    };

    return (
        <div className="flex-col bg-main min-h-screen">
            <nav className="navbar">
                <div className="logo-white" onClick={() => navigate("/schedule")}>КГУ • СЦЕНАРИИ</div>
                <div className="flex-row gap-2">
                    <button className="btn nav-btn" onClick={() => navigate("/schedule")}>К расписанию</button>
                    <button className="btn nav-btn" onClick={() => navigate("/profile")}>В профиль</button>
                </div>
            </nav>

            <div className="profile-wrapper flex-col gap-3">
                {/* Шапка страницы */}
                <div className="flex-row space-between align-center">
                    <h2 className="text-primary">Управление версиями</h2>
                    {!isCreating && (
                        <button 
                            className="btn btn-primary create-btn-margin" 
                            onClick={() => setIsCreating(true)}
                        >
                            Создать версию
                        </button>
                    )}
                </div>

                {error && (
                    <div className="error fade-in" onClick={() => setError(null)}>
                        {error}
                    </div>
                )}

                {/* Форма создания */}
                {isCreating && (
                    <div className="card slide-up flex-row gap-2 align-center bg-white">
                        <div className="flex-col f-1">
                            <label className="filter-label">Название версии</label>
                            <input 
                                className="input-styled" 
                                autoFocus
                                value={newName}
                                onChange={e => setNewName(e.target.value)}
                            />
                        </div>
                        <div className="flex-row gap-2 mt-2">
                            <button className="btn btn-green" onClick={handleCreate}>Сохранить</button>
                            <button className="btn btn-outline" onClick={() => setIsCreating(false)}>Отмена</button>
                        </div>
                    </div>
                )}

                {/* Список карточек */}
                <div className="scenario-grid slide-up">
                    {loading ? (
                        <div className="card f-1 text-center">Загрузка данных...</div>
                    ) : scenarios.length > 0 ? (
                        scenarios.map(s => (
                            <div key={s.id} className="card scenario-card">
                                <div className="flex-col">
                                    <div className="flex-row space-between align-start">
                                        <h3 className="text-primary">{s.name}</h3>
                                        {s.is_active ? (
                                            <span className="badge btn-green">Активен</span>
                                        ) : (
                                            <span className="badge btn-outline">Черновик</span>
                                        )}
                                    </div>
                                    <p className="text-muted mt-1" style={{ fontSize: '0.8rem' }}>
                                        Дата: {new Date(s.created_at).toLocaleDateString('ru-RU')}
                                    </p>
                                </div>

                                <div className="card-actions">
                                    <button 
                                        className="btn btn-primary f-1"
                                        onClick={() => navigate(`/ScheduleEditor/${s.id}`)}
                                    >
                                        Открыть
                                    </button>
                                    <button 
                                        className="btn btn-orange" 
                                        onClick={() => handleCopy(s.id)}
                                    >
                                        Копировать
                                    </button>
                                    <button 
                                        className="btn btn-red" 
                                        onClick={() => handleDelete(s.id)}
                                    >
                                        Удалить
                                    </button>
                                </div>
                            </div>
                        ))
                    ) : (
                        <div className="card f-1 text-center text-muted">Список пуст</div>
                    )}
                </div>
            </div>
        </div>
    );
};

export default ScenarioSelectionPage;