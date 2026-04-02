import { useAuth } from "@/context/AuthContext";
import { Navigate, useNavigate } from "react-router-dom";
import { useState, useEffect } from "react";
import { dbService } from "@/services/crud"; 
import type { Lesson } from "@/types/schedule"; 
import "@/styles/Profile.css";

// Интерфейс для заявок на бронирование
interface BookingRequest {
    id: number;
    classroom_num: string;
    date_start: string;
    date_end: string;
    status: number;
    description: string;
    admin_comment?: string;
}

const UserProfilePage = () => {
    const { user, logout } = useAuth();
    const navigate = useNavigate();
    
    const [myLessons, setMyLessons] = useState<Lesson[]>([]);
    const [myBookings, setMyBookings] = useState<BookingRequest[]>([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        if (user) {
            const loadProfileData = async () => {
                try {
                    // 1. Загружаем личное расписание (через экшен 'my' во вьюсете)
                    const lessonsData = await dbService.list("lessons/my");
                    setMyLessons(lessonsData);

                    // 2. Загружаем свои заявки (используем фильтр my=true)
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

    if (!user) return <Navigate to="/login" replace />;

    // Функция для определения цвета и текста статуса
    const getStatusInfo = (status: number) => {
        switch (status) {
            case 0: return { label: "На модерации", color: "var(--p-orange)", bg: "var(--bg-main)" };
            case 1: return { label: "Одобрена", color: "var(--p-green)", bg: "var(--bg-main)" };
            case 2: return { label: "Отклонена", color: "var(--p-red)", bg: "var(--bg-main)" };
            default: return { label: "Черновик", color: "var(p-blue-light)", bg: "var(--bg-main)" };
        }
    };

    return (
        <div className="flex-col bg-main min-h-screen m-0 p-0"> 
            <nav className="navbar">
                <div className="logo-white" onClick={() => navigate("/schedule")}>КГУ</div>
                <div className="flex-row gap-10">
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
                            <label className="filter-label info-label">Роль</label>
                            <span className="info-value text-primary" style={{ fontWeight: 800 }}>
                                {user ? "Администратор" : "Преподаватель / Студент"}
                            </span>
                        </div>
                    </div>

                    <div className="card slide-up" style={{ borderColor: 'var(--p-orange)' }}>
                        <h3 className="text-orange">Действия</h3>
                            <div className="action-buttons">
                                <button className="btn btn-orange" onClick={() => navigate("/schedule")}>
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
                        <div className="flex-col mt-10">
                            {!loading && myBookings.length > 0 ? (
                                myBookings.map(req => {
                                    const status = getStatusInfo(req.status);
                                    return (
                                        <div key={req.id} className="list-item flex-col" style={{ alignItems: 'stretch' }}>
                                            <div className="flex-row justify-between align-center">
                                                <div style={{ fontWeight: 600 }}>Бронь аудитории {req.classroom_num}</div>
                                                <span style={{ 
                                                    fontSize: '12px', 
                                                    padding: '4px 12px', 
                                                    borderRadius: '20px', 
                                                    backgroundColor: status.bg, 
                                                    color: status.color,
                                                    fontWeight: 700 
                                                }}>
                                                    {status.label.toUpperCase()}
                                                </span>
                                            </div>
                                            <div style={{ fontSize: '12px', marginTop: '5px' }}>
                                                {new Date(req.date_start).toLocaleString('ru-RU')}
                                            </div>
                                            {req.admin_comment && (
                                                <div className="mt-10 p-10 bg-main" style={{ borderRadius: '8px', borderLeft: `4px solid ${status.color}`, fontSize: '13px' }}>
                                                    <strong>Комментарий:</strong> {req.admin_comment}
                                                </div>
                                            )}
                                        </div>
                                    );
                                })
                            ) : (
                                <p className="empty-text">Активных заявок не найдено</p>
                            )}
                        </div>
                    </div>
                </div>

            </div>
        </div>
    );
};

export default UserProfilePage;