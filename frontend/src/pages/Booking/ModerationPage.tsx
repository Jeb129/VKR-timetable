import { useState, useEffect } from "react";
import { dbService } from "@/services/crud";
import { useNavigate } from "react-router-dom";
import "./Moderation.css"; 

const ModerationPage = () => {
    const navigate = useNavigate();
    const [requests, setRequests] = useState<any[]>([]);
    const [loading, setLoading] = useState(true);
    
    // Состояние для активного окна отказа
    const [rejectingId, setRejectingId] = useState<number | null>(null);
    const [comment, setComment] = useState("");

    const loadRequests = async () => {
        setLoading(true);
        try {
            // Запрашиваем только те, что "На модерации" (status=0)
            const data = await dbService.list("bookings", { status: 0 });
            setRequests(data);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => { loadRequests(); }, []);

    const handleApprove = async (id: number) => {
        if (!window.confirm("Одобрить эту заявку?")) return;
        await dbService.update("bookings", id, { status: 1 }); // 1 - VERIFIED
        loadRequests();
    };

    const handleReject = async (id: number) => {
        if (!comment) return alert("Укажите причину отказа!");
        await dbService.update("bookings", id, { 
            status: 2, // 2 - REJECTED
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
                <button className="nav-btn" onClick={() => navigate("/profile")}>В профиль</button>
            </nav>

            <div className="profile-wrapper flex-col gap-20">
                <h2 className="text-primary">Модерация заявок</h2>
                
                {loading ? (
                    <div className="card text-center">Загрузка...</div>
                ) : requests.length === 0 ? (
                    <div className="card text-center text-muted">Новых заявок пока нет</div>
                ) : (
                    <div className="flex-col gap-15">
                        {requests.map(req => (
                            <div key={req.id} className="card slide-up moderation-card">
                                <div className="flex-row justify-between align-start">
                                    <div className="flex-col gap-5">
                                        <div className="flex-row align-center gap-10">
                                            <span className="badge-user">👤 {req.user_name || "Пользователь"}</span>
                                            <span className="text-muted">{new Date(req.date_start).toLocaleDateString()}</span>
                                        </div>
                                        <h3 className="mt-10">Аудитория {req.classroom_num || req.classroom}</h3>
                                        <p className="time-range-text">
                                            {new Date(req.date_start).toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'})} — 
                                            {new Date(req.date_end).toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'})}
                                        </p>
                                        <p className="reason-text"><strong>Причина:</strong> {req.description}</p>
                                    </div>

                                    <div className="flex-row gap-10">
                                        <button className="primary-btn bg-green" onClick={() => handleApprove(req.id)}>Одобрить</button>
                                        <button className="primary-btn bg-error" onClick={() => setRejectingId(req.id)}>Отклонить</button>
                                    </div>
                                </div>

                                {/* Поле для причины отказа (появляется только при клике) */}
                                {rejectingId === req.id && (
                                    <div className="reject-box mt-20 fade-in">
                                        <label className="filter-label">Укажите причину отказа:</label>
                                        <textarea 
                                            className="card mt-5" 
                                            value={comment}
                                            onChange={e => setComment(e.target.value)}
                                            placeholder="Например: Аудитория занята под тех. обслуживание"
                                        />
                                        <div className="flex-row gap-10 mt-10">
                                            <button className="primary-btn bg-error flex-grow" onClick={() => handleReject(req.id)}>Подтвердить отказ</button>
                                            <button className="primary-btn bg-white text-primary" style={{border: '1px solid'}} onClick={() => setRejectingId(null)}>Отмена</button>
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