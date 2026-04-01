import { useAuth } from "@/context/AuthContext";
import { Navigate, useNavigate } from "react-router-dom";
import { useState, useEffect } from "react";
import { dbService } from "@/services/crud"; // Наш CRUD сервис
import type { Lesson } from "@/types/schedule"; // Используем общие типы
import "./Profile.css";

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
            case 0: return { label: "На модерации", color: "#e69100", bg: "#fff8e1" };
            case 1: return { label: "Одобрена", color: "#2e7d32", bg: "#e8f5e9" };
            case 2: return { label: "Отклонена", color: "#d32f2f", bg: "#ffebee" };
            default: return { label: "Черновик", color: "#718096", bg: "#f8f9fa" };
        }
    };

    return (
        <div className="flex-col bg-main min-h-screen">
            {/* Хедер */}
            <nav className="navbar">
                <div className="logo-white" onClick={() => navigate("/schedule")}>КГУ</div>
                <div className="flex-row gap-10">
                    <button className="nav-btn" onClick={() => navigate("/schedule")}>К расписанию</button>
                    <button className="nav-btn" style={{ backgroundColor: '#f5222d' }} onClick={logout}>Выйти</button>
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

                    <div className="card actions-card slide-up" style={{ borderColor: '#e69100' }}>
                        <h3 style={{ color: '#e69100' }}>Действия</h3>
                        <div className="action-buttons">
                            {/* Подать заявку на перенос (пока заглушка или на ту же страницу) */}
                            <button className="primary-btn bg-orange hover-lift" onClick={() => navigate("/schedule")}>
                                Перенести занятие
                            </button>
                            {/* Кнопка бронирования теперь функциональна */}
                            <button className="primary-btn bg-green hover-lift" onClick={() => navigate("/booking")}>
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
                        <div className="flex-col mt-10">
                            {loading ? (
                                <p className="empty-text">Загрузка...</p>
                            ) : myLessons.length > 0 ? (
                                myLessons.map(lesson => (
                                    <div key={lesson.id} className="list-item flex-row align-center">
                                        <div style={{ fontWeight: 800, width: '120px', color: '#2c3ab3' }}>
                                            {lesson.start}
                                        </div>
                                        <div className="flex-grow">
                                            <div style={{ fontWeight: 600, fontSize: '16px' }}>{lesson.discipline_name}</div>
                                            <div style={{ fontSize: '13px', color: '#718096' }}>
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
                                            <div style={{ fontSize: '12px', color: '#888', marginTop: '5px' }}>
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