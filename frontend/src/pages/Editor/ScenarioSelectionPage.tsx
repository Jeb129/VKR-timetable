import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { dbService } from "@/services/crud";
import { type ScheduleScenario } from "@/types/schedule";
import "@/styles/Editor.css"; 


const ScenarioSelectionPage = () => {
    const navigate = useNavigate();
    const [scenarios, setScenarios] = useState<ScheduleScenario[]>([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        const fetchScenarios = async () => {
            try {
                const data = await dbService.list("scenarios");
                setScenarios(data);
            } catch (err) {
                console.error("Ошибка загрузки сценариев", err);
            } finally {
                setLoading(false);
            }
        };
        fetchScenarios();
    }, []);

    return (
        <div className="flex-col bg-main min-h-screen">
            <nav className="navbar">
                <div className="logo-white" onClick={() => navigate("/schedule")}>КГУ • УПРАВЛЕНИЕ ВЕРСИЯМИ</div>
                <button className="btn nav-btn" onClick={() => navigate("/profile")}>В профиль</button>
            </nav>

            <div className="profile-wrapper flex-col gap-3">
                <div className="flex-row space-between align-center">
                    <h2 className="text-primary">Выберите версию для редактирования</h2>
                </div>

                <div className="flex-row flex-wrap gap-2 slide-up">
                    {loading ? (
                        <div className="card f-1 text-center">Загрузка...</div>
                    ) : scenarios.length > 0 ? (
                        scenarios.map(s => (
                            <div key={s.id} className="card flex-col gap-2" style={{ minWidth: '300px', flex: '1 1 300px' }}>
                                <div className="flex-row space-between align-start">
                                    <h3 className="text-primary">{s.name}</h3>
                                    {s.is_active && <span className="badge btn-green">Активно</span>}
                                </div>
                                <p className="text-muted" style={{fontSize: '0.9rem'}}>
                                    Дата создания: {new Date(s.created_at).toLocaleDateString()}
                                </p>
                                <button 
                                    className="btn btn-primary w-100" 
                                    onClick={() => navigate(`/ScheduleEditor/${s.id}`)}
                                >
                                    Открыть редактор
                                </button>
                            </div>
                        ))
                    ) : (
                        <div className="card f-1 text-center text-muted">Сценарии не найдены</div>
                    )}
                </div>
            </div>
        </div>
    );
};

export default ScenarioSelectionPage;