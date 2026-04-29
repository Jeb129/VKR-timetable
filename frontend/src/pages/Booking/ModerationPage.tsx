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

    const [bookings, setBookings] = useState<any[]>([]);
    const [adjustments, setAdjustments] = useState<any[]>([]);
    const [tab, setTab] = useState<"bookings" | "adjustments">("bookings");
    
    // Для окна отклонения
    const [rejectingId, setRejectingId] = useState<number | null>(null);
    const [adminComment, setAdminComment] = useState("");

    const getApiPath = () => tab === "bookings" ? "bookings" : "schedule/adjustments";

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

    // Вспомогательная функция для рендера зоны отказа (вынеси её внутрь компонента перед return)
    function renderRejectBox(id: number) {
        return (
            <div className="mt-2 p-2 rounded-md fade-in" style={{ border: '2px solid var(--p-red)', backgroundColor: '#fff5f5' }}>
                <label className="filter-label">Причина отказа (будет отправлена в письме):</label>
                <textarea 
                    className="input-styled mt-1" 
                    rows={3}
                    autoFocus
                    value={adminComment}
                    onChange={e => setAdminComment(e.target.value)}
                    placeholder="Например: Аудитория занята другим мероприятием..."
                />
                <div className="flex-row gap-2 mt-1">
                    <button className="btn btn-red f-1" onClick={() => handleReject(id)}>Подтвердить отклонение</button>
                    <button className="btn btn-outline f-1" onClick={() => {setRejectingId(null); setAdminComment("");}}>Отмена</button>
                </div>
            </div>
        );
    }

    return (
        <div className="flex-col bg-main min-h-screen">
            {/* ХЕДЕР С ТАБАМИ */}
            <nav className="navbar">
                <div className="flex-row align-center gap-3">
                    <div className="logo-white" onClick={() => navigate("/")}>КГУ • МОДЕРАЦИЯ</div>
                    <div className="flex-row gap-1 ml-2">
                        <button 
                            className={`btn nav-btn ${tab === "bookings" ? "btn-primary" : ""}`} 
                            onClick={() => { setTab("bookings"); setRejectingId(null); }}
                        >
                            Бронирования ({bookings.length})
                        </button>
                        <button 
                            className={`btn nav-btn ${tab === "adjustments" ? "btn-primary" : ""}`} 
                            onClick={() => { setTab("adjustments"); setRejectingId(null); }}
                        >
                            Переносы пар ({adjustments.length})
                        </button>
                    </div>
                </div>
                <button className="btn nav-btn" onClick={() => navigate("/profile")}>В профиль</button>
            </nav>

            <div className="profile-wrapper flex-col gap-2">
                <div className="flex-row space-between align-center mb-1">
                    <h2 className="text-primary">
                        {tab === "bookings" ? "Заявки на бронирование" : "Заявки на перенос занятий"}
                    </h2>
                    {error && (
                        <div className="error fade-in" style={{ margin: 0 }} onClick={() => setError(null)}>
                            {error}
                        </div>
                    )}
                </div>

                {loading ? (
                    <div className="card text-center">Загрузка данных...</div>
                ) : (
                    <div className="flex-col gap-2 slide-up">
                        {/* ЛОГИКА ОТОБРАЖЕНИЯ БРОНИРОВАНИЙ */}
                        {tab === "bookings" && (
                            bookings.length > 0 ? bookings.map(req => (
                                <div key={req.id} className="card moderation-card">
                                    <div className="flex-row space-between align-start">
                                        <div className="flex-col gap-1">
                                            <div className="flex-row align-center gap-2">
                                                <span className="badge-user">Пользователь: {req.user_name || req.user}</span>
                                                <span className="text-muted">{new Date(req.date_start).toLocaleDateString()}</span>
                                            </div>
                                            <h3 className="mt-1">Аудитория {req.classroom_num}</h3>
                                            <p className="time-range-text" style={{fontWeight: 800, fontSize: '1.2rem'}}>
                                                {new Date(req.date_start).toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'})} — 
                                                {new Date(req.date_end).toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'})}
                                            </p>
                                            <div className="reason-text p-1 bg-main rounded-md mt-1">
                                                <strong>Цель:</strong> {req.description}
                                            </div>
                                        </div>

                                        <div className="flex-row gap-1">
                                            <button className="btn btn-green" onClick={() => handleApprove( req.id)}>Одобрить</button>
                                            <button className="btn btn-red" onClick={() => setRejectingId(req.id)}>Отклонить</button>
                                        </div>
                                    </div>

                                    {rejectingId === req.id && renderRejectBox(req.id)}
                                </div>
                            )) : <div className="card text-center text-muted">Заявок на бронь нет</div>
                        )}

                        {/* ЛОГИКА ОТОБРАЖЕНИЯ ПЕРЕНОСОВ ПАР */}
                        {tab === "adjustments" && (
                            adjustments.length > 0 ? adjustments.map(adj => (
                                <div key={adj.id} className="card moderation-card" style={{borderColor: 'var(--p-orange)'}}>
                                    <div className="flex-row space-between align-start">
                                        <div className="flex-col gap-1 f-1">
                                            <div className="flex-row align-center gap-2">
                                                <span className="badge-user" style={{backgroundColor: 'var(--p-blue-light)'}}>
                                                    Преподаватель: {adj.teacher_name || adj.user_name}
                                                </span>
                                            </div>
                                            <h3 className="text-primary mt-1">{adj.lesson_name}</h3>
                                            
                                            {/* Сравнение БЫЛО / СТАНЕТ */}
                                            <div className="flex-row gap-2 mt-1 align-center">
                                                <div className="flex-col p-1 bg-main rounded-md" style={{minWidth: '150px'}}>
                                                    <small className="text-muted">БЫЛО (день {adj.old_day})</small>
                                                    <strong>{adj.old_time}</strong>
                                                </div>
                                                <span style={{fontSize: '24px', color: 'var(--p-blue)'}}>→</span>
                                                <div className="flex-col p-1 bg-white rounded-md" style={{minWidth: '180px', border: '2px solid var(--p-green)'}}>
                                                    <small className="text-muted">НОВАЯ ДАТА: {new Date(adj.date).toLocaleDateString()}</small>
                                                    <strong className="text-green">{adj.new_time} (пара {adj.new_order})</strong>
                                                </div>
                                            </div>

                                            <div className="reason-text p-1 bg-main rounded-md mt-1">
                                                <strong>Причина переноса:</strong> {adj.description}
                                            </div>
                                        </div>

                                        <div className="flex-row gap-1">
                                            <button className="btn btn-green" onClick={() => handleApprove( adj.id)}>Одобрить</button>
                                            <button className="btn btn-red" onClick={() => setRejectingId(adj.id)}>Отклонить</button>
                                        </div>
                                    </div>

                                    {rejectingId === adj.id && renderRejectBox(adj.id)}
                                </div>
                            )) : <div className="card text-center text-muted">Заявок на перенос нет</div>
                        )}
                    </div>
                )}
            </div>
        </div>
    );
};

export default ModerationPage;