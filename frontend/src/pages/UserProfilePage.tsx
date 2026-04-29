import { useAuth } from "@/context/AuthContext";
import { Navigate, useNavigate } from "react-router-dom";
import { useState, useEffect } from "react";
import { dbService } from "@/services/crud"; 
import { privateApi } from "@/services/axios";
import type { Lesson } from "@/types/schedule"; 
import type { BookingRequest } from "@/types/booking";
import "@/styles/Profile.css";

const UserProfilePage = () => {
    const { user, logout, refreshUser  } = useAuth();
    const navigate = useNavigate();
    const [myLessons, setMyLessons] = useState<Lesson[]>([]);
    const [myBookings, setMyBookings] = useState<BookingRequest[]>([]);
    const [loading, setLoading] = useState(true);
    const [isVerifying, setIsVerifying] = useState(false);
    const [verifyError, setVerifyError] = useState<string | null>(null);

    useEffect(() => {
        if (user) {
            const loadProfileData = async () => {
                try {
                    const today = new Date().toISOString().split('T')[0];

                    const lessonsParams = {
                        teacher_id: user.id, 
                        date_from: today,
                        date_to: today
                    };

                    const lessonsData = await dbService.list("schedule/teacher", lessonsParams);
                    setMyLessons(lessonsData);

                    // ЗАГРУЗКА БРОНИ 
                    const bookingsData = await dbService.list("bookings", { my: 'true' });
                    setMyBookings(bookingsData);

                } catch (err) {
                    console.error("Ошибка при загрузке данных профиля:", err);
                } finally {
                    setLoading(false);
                }
            };
            loadProfileData();
        }
    }, [user]);

    const handleMoodleVerify = async () => {
        setIsVerifying(true);
        setVerifyError(null);
        try {
            await privateApi.post("/auth/moodle-verify/"); 
            // Обновляем данные пользователя в глобальном стейте
            await refreshUser();
        } catch (err: any) {
            setVerifyError(err.response?.data?.error || "Ошибка подтверждения");
        } finally {
            setIsVerifying(false);
        }
    };

    if (!user) return <Navigate to="/login" replace />;
    // Функция для определения цвета и текста статуса
    const getStatusInfo = (status: number) => {
        switch (status) {
            case 0: return { label: "На модерации", color: "var(--p-orange)" };
            case 1: return { label: "Одобрена", color: "var(--p-green)" };
            case 2: return { label: "Отклонена", color: "var(--p-red)" };
            default: return { label: "Черновик", color: "var(--text-muted)" };
        }
    };

    return (
        <div className="flex-col bg-main min-h-screen m-0 p-0"> 
            <nav className="navbar">
                <div className="logo-white" onClick={() => navigate("/")}>КГУ</div>
                <div className="flex-row gap-10">
                    <button className="btn nav-btn" onClick={() => navigate("/")}>Главная</button>
                    <button className="btn nav-btn" onClick={() => navigate("/schedule")}>К расписанию</button>
                    <button className="btn nav-btn btn-red" onClick={logout}>Выйти</button>
                </div>
            </nav>

            <div className="profile-wrapper flex-row gap-20 align-start">
                
                {/* ЛЕВАЯ КОЛОНКА */}
                <div className="profile-sidebar flex-col gap-20">
                    <div className="card slide-up">
                        <h3 className="mb-20">Мой профиль</h3>
                        
                        <div className="info-group flex-col">
                            <label className="filter-label info-label">Логин</label>
                            <span className="info-value">{user.username}</span>
                        </div>
                        
                        <div className="info-group flex-col">
                            <label className="filter-label info-label">Email</label>
                            <span className="info-value">{user.email}</span>
                        </div>

                        <div className="info-group flex-col">
                            <label className="filter-label info-label">Роль в системе</label>
                            <span className="info-value text-primary" style={{ fontWeight: 800 }}>
                                {user.internal_user ? "Сотрудник / Студент КГУ" : "Внешний пользователь"}
                            </span>
                        </div>

                        {/* БЛОК ПОДТВЕРЖДЕНИЯ MOODLE */}
                        <div className="info-group flex-col mt-2 pt-2">
                            <label className="filter-label info-label">Статус подтверждения</label>
                            {user.internal_user ? (
                                <span className="text-green" style={{ fontWeight: 700 }}>Аккаунт подтвержден</span>
                            ) : (
                                <div className="flex-col gap-1">
                                    <button 
                                        className="btn btn-primary w-100" 
                                        onClick={handleMoodleVerify}
                                        disabled={isVerifying}
                                    >
                                        {isVerifying ? "Проверка..." : "Подтвердить через Moodle"}
                                    </button>
                                    {verifyError && (
                                        <span className="text-red mt-1" style={{ fontSize: '13px', textAlign: 'center' }}>
                                            {verifyError}
                                        </span>
                                    )}
                                </div>
                            )}
                        </div>
                    </div>

                    <div className="card slide-up" style={{ borderColor: 'var(--p-orange)' }}>
                        <h3 className="text-orange">Действия</h3>
                            <div className="action-buttons">
                                <button className="btn btn-orange" onClick={() => navigate("/TeacherAdjustment")}>
                                    Перенести занятие
                                </button>
                                <button className="btn btn-green" onClick={() => navigate("/booking")}>
                                    Забронировать ауд.
                                </button>
                            </div>
                    </div>
                </div>

                {/* ПРАВАЯ КОЛОНКА */}
                <div className="content-area flex-grow">
                    
                    {/* Моё расписание */}
                    <div className="card fade-in">
                        <h3>Моё ближайшее расписание</h3>
                        <div className="flex-col mt-2">
                            {myLessons.length > 0 ? (
                                myLessons.map(lesson => (
                                    <div key={lesson.id} className="list-item flex-row align-center">
                                        <div className="text-primary" style={{ fontWeight: 800, width: '120px' }}>
                                            {lesson.start}
                                        </div>
                                        <div className="flex-grow">
                                            <div style={{ fontWeight: 600 }}>{lesson.discipline_name}</div>
                                            <div className="text-muted" style={{ fontSize: '13px' }}>
                                                Кабинет {lesson.classroom_name} • {lesson.type_name}
                                            </div>
                                        </div>
                                    </div>
                                ))
                            ) : (
                                <p className="empty-text">У вас пока нет назначенных занятий</p>
                            )}
                        </div>
                    </div>

                    {/* Статус заявок */}
                    <div className="card fade-in">
                        <h3>Статус моих заявок</h3>
                        <div className="flex-col mt-2">
                            {myBookings.length > 0 ? (
                                myBookings.map(req => {
                                    const status = getStatusInfo(req.status);
                                    return (
                                        <div key={req.id} className="list-item flex-col">
                                            <div className="flex-row space-between align-center">
                                                <div style={{ fontWeight: 700 }}>Бронь аудитории {req.classroom_num}</div>
                                                <span className="badge" style={{ 
                                                    backgroundColor: 'var(--bg-main)', 
                                                    color: status.color,
                                                    border: `1px solid ${status.color}`
                                                }}>
                                                    {status.label}
                                                </span>
                                            </div>
                                            <div className="text-muted mt-1" style={{ fontSize: '13px' }}>
                                                {new Date(req.date_start).toLocaleString('ru-RU', { day: 'numeric', month: 'long', hour: '2-digit', minute: '2-digit' })}
                                            </div>
                                            
                                            {/* Комментарий админа */}
                                            {req.admin_comment && (
                                                <div className="bg-main mt-1" style={{ borderLeft: `4px solid ${status.color}`, padding: '10px', borderRadius: '8px' }}>
                                                    <small><strong>Комментарий модератора:</strong></small>
                                                    <p style={{ fontSize: '13px', margin: '4px 0 0 0' }}>{req.admin_comment}</p>
                                                </div>
                                            )}
                                        </div>
                                    );
                                })
                            ) : (
                                <p className="empty-text">История заявок пуста</p>
                            )}
                        </div>
                    </div>
                </div>

            </div>
        </div>
    );
};

export default UserProfilePage;