// frontend/src/pages/UserProfilePage.tsx
import { useAuth } from "@/context/AuthContext";
import { Navigate, useNavigate } from "react-router-dom";
import { useState, useEffect } from "react";
import axios from "axios";
import "./Profile.css"; // Импорт новых стилей

interface Lesson {
    id: number;
    discipline_name: string;
    type_name: string;
    classroom_name: string;
    start: string;
    end: string;
    order: number;
    day: number;
    teachers_list: string[];
    groups_list: string[];
}

const UserProfilePage = () => {
    const { user, logout } = useAuth();
    const navigate = useNavigate();
    const [myLessons, setMyLessons] = useState<Lesson[]>([]);

    useEffect(() => {
        axios.get("http://localhost:8000/api/lessons/my/")
            .then(res => setMyLessons(res.data))
            .catch(err => console.error("Ошибка загрузки", err));
    }, []);

    if (!user) return <Navigate to="/login" replace />;

    return (
        <div className="flex-col bg-main min-h-screen">
            {/* Хедер остается без изменений */}
            <nav className="navbar">
                <div className="logo-white" onClick={() => navigate("/schedule")}>КГУ</div>
                <div className="flex-row gap-10">
                    <button className="nav-btn" onClick={() => navigate("/schedule")}>К расписанию</button>
                    <button className="nav-btn" style={{backgroundColor: '#f5222d'}} onClick={logout}>Выйти</button>
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
                            <span className="info-value text-primary" style={{fontWeight: 800}}>Преподаватель</span>
                        </div>
                    </div>

                    <div className="card actions-card slide-up" style={{borderColor: '#e69100'}}>
                        <h3 style={{color: '#e69100'}}>Действия</h3>
                        <div className="action-buttons">
                            <button className="primary-btn bg-orange hover-lift">Подать заявку</button>
                            <button className="primary-btn bg-green hover-lift">Забронировать ауд.</button>
                        </div>
                    </div>
                </div>

                {/* ПРАВАЯ КОЛОНКА */}
                <div className="content-area flex-grow">
                    <div className="card fade-in">
                        <h3>Моё ближайшее расписание</h3>
                        <div className="flex-col mt-10">
                            {myLessons.length > 0 ? (
                                myLessons.map(lesson => (
                                    <div key={lesson.id} className="list-item flex-row align-center">
                                        <div style={{fontWeight: 800, width: '120px', color: '#2c3ab3'}}>{lesson.start}</div>
                                        <div className="flex-grow">
                                            <div style={{fontWeight: 600, fontSize: '16px'}}>{lesson.discipline_name}</div>
                                            <div style={{fontSize: '13px', color: '#718096'}}>Кабинет {lesson.classroom_name} • {lesson.type_name}</div>
                                        </div>
                                    </div>
                                ))
                            ) : (
                                <p className="empty-text">У вас пока нет назначенных занятий на сегодня</p>
                            )}
                        </div>
                    </div>

                    <div className="card fade-in">
                        <h3>Статус моих заявок</h3>
                        <div className="empty-text">Активных заявок не найдено</div>
                    </div>
                </div>

            </div>
        </div>
    );
};

export default UserProfilePage;