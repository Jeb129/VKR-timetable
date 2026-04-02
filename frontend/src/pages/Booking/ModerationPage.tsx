import { useState, useEffect } from "react";
import { dbService } from "@/services/crud";
import { useNavigate } from "react-router-dom";
import "@/styles/Moderation.css"; 

const ModerationPage = () => {
    const navigate = useNavigate();
    const [requests, setRequests] = useState<any[]>([]);
    const [loading, setLoading] = useState(true);
    
    const [rejectingId, setRejectingId] = useState<number | null>(null);
    const [comment, setComment] = useState("");

    const loadRequests = async () => {
        setLoading(true);
        try {
            // Используем системный метод list
            const data = await dbService.list("bookings", { status: 0 });
            setRequests(data);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => { loadRequests(); }, []);

    const handleApprove = async (id: number) => {
        if (!window.confirm("Одобрить эту заявку?")) return;
        await dbService.update("bookings", id, { status: 1 });
        loadRequests();
    };

    const handleReject = async (id: number) => {
        if (!comment) return alert("Укажите причину отказа!");
        await dbService.update("bookings", id, { 
            status: 2, 
            admin_comment: comment 
        });
        setRejectingId(null);
        setComment("");
        loadRequests();
    };

    return (
        <div className="flex-col bg-main min-h-screen">
            <nav className="navbar">
                <div className="logo-white" onClick={() => navigate("/schedule")}>КГУ • АДМИН</div>
                <button className="btn nav-btn" onClick={() => navigate("/profile")}>В профиль</button>
            </nav>

            <div className="moderation-wrapper flex-col gap-3">
                <h2 className="text-primary">Модерация заявок</h2>
                
                {loading ? (
                    <div className="card text-center">Загрузка...</div>
                ) : requests.length === 0 ? (
                    <div className="card text-center text-muted">Новых заявок пока нет</div>
                ) : (
                    <div className="flex-col gap-2 slide-up">
                        {requests.map(req => (
                            <div key={req.id} className={`card moderation-card ${rejectingId === req.id ? 'is-rejecting' : ''}`}>
                                <div className="flex-row space-between align-start">
                                    <div className="flex-col gap-1">
                                        <div className="flex-row align-center gap-2">
                                            <span className="badge-user">👤 {req.user_name}</span>
                                            <span className="text-muted">{new Date(req.date_start).toLocaleDateString()}</span>
                                        </div>
                                        <h3 className="mt-1">Аудитория {req.classroom_num}</h3>
                                        <p className="time-range-text">
                                            {new Date(req.date_start).toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'})} — 
                                            {new Date(req.date_end).toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'})}
                                        </p>
                                        <div className="reason-box">
                                            <strong>Причина:</strong> {req.description}
                                        </div>
                                    </div>

                                    <div className="flex-row gap-2">
                                        <button className="btn btn-green" onClick={() => handleApprove(req.id)}>Одобрить</button>
                                        <button className="btn btn-red" onClick={() => setRejectingId(req.id)}>Отклонить</button>
                                    </div>
                                </div>

                                {rejectingId === req.id && (
                                    <div className="reject-container fade-in">
                                        <label className="filter-label">Укажите причину отказа:</label>
                                        <textarea 
                                            className="input-styled mt-1" 
                                            rows={3}
                                            value={comment}
                                            onChange={e => setComment(e.target.value)}
                                            placeholder="Опишите причину здесь..."
                                        />
                                        <div className="flex-row gap-2 mt-2">
                                            <button className="btn btn-red f-1" onClick={() => handleReject(req.id)}>Подтвердить отказ</button>
                                            <button className="btn btn-outline" onClick={() => setRejectingId(null)}>Отмена</button>
                                        </div>
                                    </div>
                                )}
                            </div>
                        ))}
                    </div>
                )}
            </div>
        </div>
    );
};

export default ModerationPage;