import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { dbService } from "@/services/crud";
// import type { BookingRequest } from "@/types/booking";
import "@/styles/Moderation.css"; 

const ModerationPage = () => {
    const navigate = useNavigate();
    // const [requests, setRequests] = useState<BookingRequest[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    const [bookings, setBookings] = useState<any[]>([]);
    const [adjustments, setAdjustments] = useState<any[]>([]);
    const [tab, setTab] = useState<"bookings" | "adjustments">("bookings");
    
    // Для окна отклонения
    const [rejectingId, setRejectingId] = useState<number | null>(null);
    const [adminComment, setAdminComment] = useState("");

    // const getApiPath = () => tab === "bookings" ? "bookings" : "schedule/adjustments";

    const loadRequests = async () => {
        setLoading(true);
        try {
            // Загружаем оба типа заявок со статусом 0 (На модерации)
            const [bData, aData] = await Promise.all([
                dbService.list("bookings", { status: 0 }),
                dbService.list("schedule/adjustments", { status: 0 })
            ]);
            setBookings(bData);
            setAdjustments(aData);
        } catch (err) {
            setError("Ошибка при подгрузке данных");
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => { loadRequests(); }, []);

    // Универсальный метод одобрения
    const handleApprove = async (id: number) => {
        setError(null);
        try {
            const path = tab === "bookings" ? "bookings" : "schedule/adjustments";
            // Вызываем новый специализированный метод
            await dbService.approveRequest(path, id);
            loadRequests();
        } catch (err: any) {
            setError("Ошибка при одобрении: " + (err.response?.data?.detail || "сервер недоступен"));
        }
    };
    

    const handleReject = async (id: number) => {
        setError(null);
        if (!adminComment) {
            setError("Пожалуйста, укажите причину отклонения");
            return;
        }
        try {
            const path = tab === "bookings" ? "bookings" : "schedule/adjustments";
            await dbService.rejectRequest(path, id, adminComment);
            
            setRejectingId(null);
            setAdminComment("");
            loadRequests();
        } catch (err: any) {
            setError("Ошибка при отклонении: " + (err.response?.data?.detail || "сервер недоступен"));
        }
    };

    const formatDate = (d: string) => new Date(d).toLocaleDateString('ru-RU', { day: 'numeric', month: 'long' });
    const formatTime = (d: string) => new Date(d).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });

    return (
        <div className="flex-col bg-main min-h-screen">
            <nav className="navbar flex-row space-between align-center">
                <div className="flex-row align-center gap-3">
                    <div className="logo-white" onClick={() => navigate("/")} style={{cursor: 'pointer'}}>КГУ • МОДЕРАЦИЯ</div>
                    <div className="flex-row gap-1">
                        <button className={`btn nav-btn ${tab === "bookings" ? "btn-primary" : ""}`} onClick={() => setTab("bookings")}>
                            Бронирования ({bookings.length})
                        </button>
                        <button className={`btn nav-btn ${tab === "adjustments" ? "btn-primary" : ""}`} onClick={() => setTab("adjustments")}>
                            Переносы ({adjustments.length})
                        </button>
                    </div>
                </div>
                <button className="btn nav-btn" onClick={() => navigate("/profile")}>В профиль</button>
            </nav>

            <div className="moderation-wrapper flex-col gap-2">
                {error && <div className="error mb-2" onClick={() => setError(null)}>{error}</div>}

                {loading ? (
                    <div className="card text-center">Загрузка данных...</div>
                ) : (
                    <div className="flex-col slide-up">
                        {/* ВКЛАДКА БРОНИРОВАНИЙ */}
                        {tab === "bookings" && bookings.map(req => (
                            <div key={req.id} className="card moderation-card p-0 no-scroll">
                                <div className="p-3">
                                    <div className="flex-row space-between align-start">
                                        <div className="flex-col f-1">
                                            <div className="flex-row align-center">
                                                <span className="badge-user">Пользователь: ({req.user_name})</span>
                                                <span className="booking-type-tag">{req.booking_type_name}</span>
                                            </div>
                                            
                                            <div className="request-info-grid">
                                                <div className="info-item">
                                                    <label>Аудитория</label>
                                                    <span>{req.classroom_num}</span>
                                                </div>
                                                <div className="info-item">
                                                    <label>Дата</label>
                                                    <span>{formatDate(req.date_start)}</span>
                                                </div>
                                                <div className="info-item">
                                                    <label>Время</label>
                                                    <span>{formatTime(req.date_start)} — {formatTime(req.date_end)}</span>
                                                </div>
                                            </div>

                                            <div className="reason-box">
                                                <strong>Цель брони:</strong> {req.description}
                                            </div>
                                        </div>

                                        <div className="flex-row gap-1">
                                            <button className="btn btn-green" onClick={() => handleApprove(req.id)}>Одобрить</button>
                                            <button className="btn btn-red" onClick={() => setRejectingId(req.id)}>Отклонить</button>
                                        </div>
                                    </div>
                                </div>
                                {rejectingId === req.id && (
                                    <div className="reject-area fade-in">
                                        <label className="filter-label">Укажите причину отказа:</label>
                                        <textarea className="input-styled mt-1" rows={3} value={adminComment} onChange={e => setAdminComment(e.target.value)} autoFocus />
                                        <div className="flex-row gap-2 mt-2">
                                            <button className="btn btn-red f-1" onClick={() => handleReject(req.id)}>Подтвердить отклонение</button>
                                            <button className="btn btn-outline f-1" onClick={() => setRejectingId(null)}>Отмена</button>
                                        </div>
                                    </div>
                                )}
                            </div>
                        ))}

                        {/* ВКЛАДКА ПЕРЕНОСОВ */}
                        {tab === "adjustments" && adjustments.map(adj => (
                            <div key={adj.id} className="card moderation-card card-adjustment p-0 no-scroll">
                                <div className="p-3">
                                    <div className="flex-row space-between align-start">
                                        <div className="flex-col f-1">
                                            <span className="badge-user">Преподаватель: {adj.teacher_name}</span>
                                            <h3 className="mt-1 text-primary">{adj.lesson_name}</h3>

                                            <div className="adjustment-flow mt-2">
                                                <div className="flow-step">
                                                    <label className="text-muted" style={{fontSize: '10px'}}>БЫЛО</label>
                                                    <div style={{fontWeight: 700}}>День {adj.old_day}, {adj.old_time}</div>
                                                </div>
                                                <div className="flow-arrow">→</div>
                                                <div className="flow-step">
                                                    <label className="text-muted" style={{fontSize: '10px'}}>СТАНЕТ</label>
                                                    <div className="text-green" style={{fontWeight: 800}}>
                                                        {formatDate(adj.date)}, {adj.new_time} (пара {adj.new_order})
                                                    </div>
                                                </div>
                                            </div>

                                            <div className="reason-box mt-2">
                                                <strong>Причина переноса:</strong> {adj.description}
                                            </div>
                                        </div>

                                        <div className="flex-row gap-1">
                                            <button className="btn btn-green" onClick={() => handleApprove(adj.id)}>Подтвердить</button>
                                            <button className="btn btn-red" onClick={() => setRejectingId(adj.id)}>Отклонить</button>
                                        </div>
                                    </div>
                                </div>
                                {rejectingId === adj.id && (
                                    <div className="reject-area fade-in">
                                        <label className="filter-label">Причина отказа:</label>
                                        <textarea className="input-styled mt-1" rows={3} value={adminComment} onChange={e => setAdminComment(e.target.value)} autoFocus />
                                        <div className="flex-row gap-2 mt-2">
                                            <button className="btn btn-red f-1" onClick={() => handleReject(adj.id)}>Подтвердить отклонение</button>
                                            <button className="btn btn-outline f-1" onClick={() => setRejectingId(null)}>Отмена</button>
                                        </div>
                                    </div>
                                )}
                            </div>
                        ))}

                        {((tab === "bookings" && bookings.length === 0) || (tab === "adjustments" && adjustments.length === 0)) && (
                            <div className="card text-center text-muted">Заявок в этой категории нет</div>
                        )}
                    </div>
                )}
            </div>
        </div>
    );
};

export default ModerationPage;