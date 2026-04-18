import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { dbService } from "@/services/crud";
import type { BookingRequest } from "@/types/booking";
import "@/styles/Moderation.css"; 

const ModerationPage = () => {
    const navigate = useNavigate();
    const [requests, setRequests] = useState<BookingRequest[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    
    // Для окна отклонения
    const [rejectingId, setRejectingId] = useState<number | null>(null);
    const [adminComment, setAdminComment] = useState("");

    const loadRequests = async () => {
        setLoading(true);
        try {
            // Загружаем только те, что "На модерации" (status=0)
            const data = await dbService.list("bookings", { status: 0 });
            setRequests(data);
        } catch (err) {
            console.error("Ошибка загрузки заявок:", err);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => { loadRequests(); }, []);

    const handleApprove = async (id: number) => {
        if (!window.confirm("Одобрить эту заявку?")) return;
        try {
            await dbService.update("bookings", id, { status: 1 }); // 1 - VERIFIED
            loadRequests();
        } catch (err) {
            setError("Ошибка при одобрении заявки");
        }
    };

    const handleReject = async (id: number) => {
        if (!adminComment) {
            alert("Обязательно укажите причину отказа");
            return;
        }
        try {
            await dbService.update("bookings", id, { 
                status: 2, // 2 - REJECTED
                admin_comment: adminComment 
            });
            setRejectingId(null);
            setAdminComment("");
            loadRequests();
        } catch (err) {
            setError("Ошибка при сохранении отказа");
        }
    };

    return (
        <div className="flex-col bg-main min-h-screen">
            <nav className="navbar">
                <div className="logo-white" onClick={() => navigate("/schedule")}>КГУ • МОДЕРАЦИЯ</div>
                <div className="nav-actions">
                    <button className="btn nav-btn" onClick={() => navigate("/schedule")}>К расписанию</button>
                    <button className="btn nav-btn" onClick={() => navigate("/profile")}>В профиль</button>
                </div>
            </nav>

            <div className="profile-wrapper flex-col gap-2">
                <h2 className="text-primary mb-1">Новые заявки на бронирование</h2>
                
                {loading ? (
                    <div className="card text-center">Загрузка данных...</div>
                ) : requests.length === 0 ? (
                    <div className="card text-center text-muted">Новых заявок не найдено</div>
                ) : (
                    <div className="flex-col gap-2 slide-up">
                        {requests.map(req => (
                            <div key={req.id} className="card moderation-card">
                                <div className="flex-row space-between align-start">
                                    <div className="flex-col gap-1">
                                        <div className="flex-row align-center gap-2">
                                            <span className="badge-user">Пользователь #{req.user}</span>
                                            <span className="text-muted">{new Date(req.date_start).toLocaleDateString()}</span>
                                        </div>
                                        <h3 className="mt-1">Аудитория {req.classroom_num}</h3>
                                        <p className="time-range-text" style={{fontWeight: 800, fontSize: '1.2rem'}}>
                                            {new Date(req.date_start).toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'})} — 
                                            {new Date(req.date_end).toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'})}
                                        </p>
                                        <div className="reason-text p-1 bg-main rounded-md mt-1">
                                            <strong>Причина:</strong> {req.description}
                                        </div>
                                    </div>

                                    <div className="flex-row gap-1">
                                        <button className="btn btn-green" onClick={() => handleApprove(req.id)}>Одобрить</button>
                                        <button className="btn btn-red" onClick={() => setRejectingId(req.id)}>Отклонить</button>
                                    </div>
                                </div>

                                {rejectingId === req.id && (
                                    <div className="mt-2 p-2 rounded-md" style={{ border: '2px solid var(--p-red)', backgroundColor: '#fff5f5' }}>
                                        <label className="filter-label">Причина отказа (будет видна пользователю):</label>
                                        <textarea 
                                            className="input-styled mt-1" 
                                            rows={3}
                                            value={adminComment}
                                            onChange={e => setAdminComment(e.target.value)}
                                        />
                                        <div className="flex-row gap-2 mt-1">
                                            <button className="btn btn-red f-1" onClick={() => handleReject(req.id)}>Подтвердить отказ</button>
                                            <button className="btn btn-outline f-1" onClick={() => setRejectingId(null)}>Отмена</button>
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