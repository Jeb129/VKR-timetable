import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { dbService } from "@/services/crud";
import "@/styles/Stats.css";

const StatsPage = () => {
    const navigate = useNavigate();
    const [stats, setStats] = useState<any[]>([]);

    useEffect(() => {
        dbService.list("statistics/load").then(setStats);
    }, []);

    return (
        <div className="flex-col bg-main min-h-screen">
            <nav className="navbar">
                <div className="logo-white" onClick={() => navigate("/")}>КГУ • СТАТИСТИКА</div>
                <button className="btn nav-btn" onClick={() => navigate("/profile")}>В профиль</button>
            </nav>

            <div className="profile-wrapper flex-col gap-3">
                <h2 className="text-primary">Загруженность инфраструктуры</h2>
                
                <div className="flex-row flex-wrap gap-2 slide-up">
                    { stats.map(b => (
                        <div key={b.id} className="card flex-col gap-2" style={{ flex: '1 1 350px' }} onClick={() => navigate(`/Statistics/${b.id}`)} >
                            <div className="flex-row space-between align-center">
                                <h3>Корпус {b.short_name}</h3>
                                <span className="text-primary" style={{ fontWeight: 800 }}>{b.load_percent}%</span>
                            </div>                            
                            {/* Полоска загрузки */}
                            <div className="progress-container">
                                <div 
                                    className="progress-bar" 
                                    style={{ 
                                        width: `${b.load_percent}%`,
                                        backgroundColor: b.load_percent > 70 ? 'var(--p-red)' : 'var(--p-blue)'
                                    }}
                                />
                            </div>

                            <div className="flex-row space-between text-muted" style={{ fontSize: '0.85rem' }} >
                                <span>Аудиторий: {b.rooms_count}</span>
                                
                                <span>Занятий в неделю: {b.lessons_count}</span>
                            </div>
                        </div>
                    ))}
                </div>
            </div>
        </div>
    );
};

export default StatsPage;