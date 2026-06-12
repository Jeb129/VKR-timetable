import { useState, useEffect, useCallback } from "react";
import { useNavigate } from "react-router-dom";
import { requestService } from "@/services/request"; 
import { MyTable } from "@/components/requests/MyTable"; 
import { RequestStatus } from "@/types/enums";
import type { RequestInstance } from "@/types/request";
import "@/styles/Moderation.css"; 

const ModerationPage = () => {
    const navigate = useNavigate();
    const [requests, setRequests] = useState<RequestInstance[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    // Параметры фильтрации 
    const [statusFilter, setStatusFilter] = useState<number>(RequestStatus.PENDING);

    const loadRequests = useCallback(async () => {
        setLoading(true);
        setError(null);
        try {
            // Запрашиваем через универсальный сервис
            const response = await requestService.getAll({ 
                status: statusFilter,
                page_size: 100 
            });
            
            // Твой сервис возвращает RequestsPagination, данные лежат в results
            setRequests(response.results);
        } catch (err: any) {
            setError("Не удалось загрузить список заявок. Возможно, недостаточно прав.");
            console.error(err);
        } finally {
            setLoading(false);
        }
    }, [statusFilter]);

    useEffect(() => {
        loadRequests();
    }, [loadRequests]);

    return (
        <div className="flex-col bg-main min-h-screen">
            <nav className="navbar flex-row space-between align-center">
                <div className="flex-row align-center gap-3">
                    <div className="logo-white" onClick={() => navigate("/")} style={{cursor: 'pointer'}}>
                        КГУ • МОДЕРАЦИЯ
                    </div>
                    
                    {/* Переключатель статусов */}
                    <div className="flex-row gap-1 ml-2">
                        <button 
                            className={`btn nav-btn ${statusFilter === RequestStatus.PENDING ? "btn-primary" : ""}`} 
                            onClick={() => setStatusFilter(RequestStatus.PENDING)}
                        >
                            Новые
                        </button>
                        <button 
                            className={`btn nav-btn ${statusFilter === RequestStatus.VERIFIED ? "btn-primary" : ""}`} 
                            onClick={() => setStatusFilter(RequestStatus.VERIFIED)}
                        >
                            Одобренные
                        </button>
                        <button 
                            className={`btn nav-btn ${statusFilter === RequestStatus.REJECTED ? "btn-primary" : ""}`} 
                            onClick={() => setStatusFilter(RequestStatus.REJECTED)}
                        >
                            Архив
                        </button>
                    </div>
                </div>
                <button className="btn nav-btn" onClick={() => navigate("/profile")}>В профиль</button>
            </nav>

            <div className="profile-wrapper flex-col gap-2">
                <div className="flex-row space-between align-center mb-1">
                    <h2 className="text-primary">Управление запросами</h2>
                    {error && (
                        <div className="error fade-in" style={{ margin: 0 }} onClick={() => setError(null)}>
                            {error}
                        </div>
                    )}
                </div>

                <MyTable 
                    data={requests} 
                    loading={loading} 
                    onActionSuccess={loadRequests} 
                />

                {!loading && requests.length === 0 && (
                    <div className="card text-center text-muted p-4">
                        Заявок в данной категории не найдено
                    </div>
                )}
            </div>
        </div>
    );
};

export default ModerationPage;