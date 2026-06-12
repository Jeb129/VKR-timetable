import { useAuth } from "@/context/AuthContext";
import { Navigate, useNavigate } from "react-router-dom";
import { useState, useEffect, useMemo } from "react";
import { dbService } from "@/services/crud"; 
import { privateApi } from "@/services/axios";
import { useModal } from "@/context/ModalContext"; 
import GroupPicker from "@/components/profile/GroupPicker"; 
import type { MappedEvent } from "@/types/schedule"; 
import "@/styles/Profile.css";
import { scheduleViewService } from "@/services/schedule_view";
import type { RequestInstance } from "@/types/request";
import type { User } from "@/types/user";
import { requestService } from "@/services/request";

const UserProfilePage = () => {
    const { user, logout, refreshUser } = useAuth();
    const { openModal, closeModal } = useModal();
    const navigate = useNavigate();

    const [myLessons, setMyLessons] = useState<MappedEvent[]>([]);
    const [myRequests, setMyRequests] = useState<RequestInstance[]>([]);
    const [isVerifying, setIsVerifying] = useState(false);
    const [verifyError, setVerifyError] = useState<string | null>(null);

    useEffect(() => {
        if (user) {
            const loadProfileData = async () => {
                try {
                    const today = new Date().toISOString().split('T')[0];
                    const teacherId = user.teacher?.id;
                    const studygroupId = user.study_group?.id;
                    
                    let tLessons: MappedEvent[] = []
                    let sgLessons: MappedEvent[] = []

                    if (teacherId) {
                        tLessons = await scheduleViewService.teacher(teacherId,today,today)
                    }
                    if (studygroupId) {
                        sgLessons = await scheduleViewService.group(studygroupId,today,today)
                    }
                    setMyLessons([...tLessons,...sgLessons])

                    const reqData = (await requestService.getAll({
                        search: user.email
                    })).results
                    setMyRequests(reqData)
                } catch (err) {
                    console.error("Ошибка при загрузке данных профиля:", err);
                }
            };
            loadProfileData();
        }
    }, [user]);

    // Хелпер для группировки занятий 
    const lessonsByDay = useMemo(() => {
        const groups: Record<string, MappedEvent[]> = {};
        myLessons.forEach(event => {
            const date = event.start.split('T')[0];
            if (!groups[date]) groups[date] = [];
            groups[date].push(event);
        });
        return groups;
    }, [myLessons]);

    // Модалка выбора группы
    const openGroupModal = () => {
        openModal({
            title: "Выбор учебной группы",
            content: <GroupPicker 
                onClose={closeModal} 
                onSuccess={async () => {
                    await refreshUser();
                    closeModal();
                }} 
            />
        });
    };

    const getDayLabel = (dateStr: string) => {
        const today = new Date().toISOString().split('T')[0];
        if (dateStr === today) return "Сегодня";
        return new Date(dateStr).toLocaleDateString('ru-RU', { weekday: 'long', day: 'numeric', month: 'short' });
    };

    const handleMoodleVerify = async () => {
        setIsVerifying(true);
        setVerifyError(null);
        try {
            await privateApi.post("/auth/moodle-verify/"); 
            await refreshUser();
        } catch (err: any) {
            setVerifyError(err.response?.data?.error || "Email не найден в Moodle");
        } finally {
            setIsVerifying(false);
        }
    };

    if (!user) return <Navigate to="/login" replace />;

    const getStatusInfo = (status: number) => {
        switch (status) {
            case 0: return { label: "На модерации", color: "var(--p-orange)" };
            case 1: return { label: "Одобрена", color: "var(--p-green)" };
            case 2: return { label: "Отклонена", color: "var(--p-red)" };
            default: return { label: "Черновик", color: "var(--text-muted)" };
        }
    };

    return (
        <div className="flex-col bg-main min-h-screen"> 
            <nav className="navbar">
                <div className="logo-white" onClick={() => navigate("/")} style={{cursor: 'pointer'}}>КГУ</div>
                <div className="flex-row gap-10">
                    <button className="btn nav-btn" onClick={() => navigate("/")}>Главная</button>
                    <button className="btn nav-btn" onClick={() => navigate("/schedule")}>К расписанию</button>
                    <button className="btn nav-btn btn-red" onClick={logout}>Выйти</button>
                </div>
            </nav>

            <div className="profile-wrapper flex-row gap-20 align-start">
                <div className="profile-sidebar flex-col gap-20">
                    <div className="card slide-up">
                        <h3 className="mb-2">Мой профиль</h3>
                        <div className="info-group flex-col">
                            <label className="filter-label">Логин</label>
                            <span className="info-value">{user.username}</span>
                        </div>
                        <div className="info-group flex-col">
                            <label className="filter-label">Email</label>
                            <span className="info-value">{user.email}</span>
                        </div>
                        <div className="info-group flex-col mt-2 pt-2">
                            <div className="info-group flex-col">
                                <label className="filter-label info-label">Роль в системе</label>
                                <span className="info-value text-primary" style={{ fontWeight: 800 }}>
                                    {/* ИСПОЛЬЗУЕМ is_internal */}
                                    {user.is_internal ? "Сотрудник / Студент КГУ" : "Внешний пользователь"}
                                </span>
                            </div>

                            {/* БЛОК ПОДТВЕРЖДЕНИЯ MOODLE */}
                            <div className="info-group flex-col mt-2 pt-2">
                                <label className="filter-label info-label">Статус подтверждения</label>
                                {user.is_internal ? ( // ИСПОЛЬЗУЕМ is_internal
                                    <div className="flex-col gap-1">
                                        <span className="text-green" style={{ fontWeight: 700 }}>Аккаунт подтвержден через Moodle</span>
                                        
                                        {/* Проверяем наличие привязанной группы через объект */}
                                        {user.study_group ? (
                                            <div className="bg-main p-1 rounded-md mt-1">
                                                <small className="text-muted">Группа: </small>
                                                <strong>{user.study_group.name}</strong>
                                            </div>
                                        ) : (
                                            <button className="btn btn-orange w-100 mt-1" onClick={openGroupModal}>
                                                Выбрать группу
                                            </button>
                                        )}
                                    </div>
                                ) : (
                                    <div className="flex-col gap-1">
                                        <button 
                                            className="btn btn-primary w-100" 
                                            onClick={handleMoodleVerify}
                                            disabled={isVerifying}
                                        >
                                            {isVerifying ? "Проверка..." : "Подтвердить через Moodle"}
                                        </button>
                                        {verifyError && <span className="text-red mt-1">{verifyError}</span>}
                                    </div>
                                )}
                            </div>
                        </div>
                    </div>

                    <div className="card slide-up" style={{ borderColor: 'var(--p-orange)' }}>
                        <h3 className="text-orange">Действия</h3>
                        <div className="action-buttons flex-col gap-1">
                            <button className="btn btn-orange" onClick={() => navigate("/TeacherAdjustment")}>Перенести занятие</button>
                            <button className="btn btn-green" onClick={() => navigate("/booking")}>Забронировать ауд.</button>
                        </div>
                    </div>
                </div>

                <div className="content-area flex-grow">
                    <div className="card fade-in">
                        <h3>Ближайшие занятия</h3>
                        <div className="flex-col mt-2 gap-2">
                            {user.is_internal ? (
                                Object.keys(lessonsByDay).length > 0 ? (
                                    Object.entries(lessonsByDay).map(([date, dayLessons]) => (
                                        <div key={date} className="flex-col">
                                            <div className="text-muted mb-1" style={{ fontSize: '12px', fontWeight: 700, textTransform: 'uppercase' }}>
                                                {getDayLabel(date)}
                                            </div>
                                            {dayLessons.map((item, idx) => (
                                                <div key={idx} className="list-item flex-row align-center py-1">
                                                    <div className="text-primary" style={{ fontWeight: 800, width: '90px' }}>
                                                        {new Date(item.start).toLocaleTimeString('ru-RU', {hour: '2-digit', minute:'2-digit'})}
                                                    </div>
                                                    <div className="flex-grow">
                                                        <div style={{ fontWeight: 600 }}>{item.extendedProps.event.discipline}</div>
                                                        <div className="text-muted" style={{ fontSize: '13px' }}>
                                                            {item.extendedProps.event.classroom} • {item.extendedProps.event.lesson_type}
                                                        </div>
                                                    </div>
                                                </div>
                                            ))}
                                        </div>
                                    ))
                                ) : (
                                    <p className="empty-text">На ближайшие два дня занятий не найдено</p>
                                )
                            ) : (
                                <p className="empty-text">Подтвердите аккаунт, чтобы видеть своё расписание</p>
                            )}
                        </div>
                    </div>

                    <div className="card fade-in">
                        <h3>Статус моих заявок</h3>
                        <div className="flex-col mt-2">
                            {/* {myBookings.length > 0 ? (
                                myBookings.map(req => {
                                    const status = getStatusInfo(req.status);
                                    return (
                                        <div key={req.id} className="list-item flex-col">
                                            <div className="flex-row space-between align-center">
                                                <div style={{ fontWeight: 700 }}>Бронь аудитории {req.classroom_num}</div>
                                                <span className="badge" style={{ color: status.color, border: `1px solid ${status.color}` }}>
                                                    {status.label}
                                                </span>
                                            </div>
                                            <div className="text-muted mt-1" style={{ fontSize: '13px' }}>
                                                {new Date(req.date_start).toLocaleString('ru-RU')}
                                            </div>
                                            {req.admin_comment && (
                                                <div className="bg-main mt-1" style={{ borderLeft: `4px solid ${status.color}`, padding: '10px', borderRadius: '8px' }}>
                                                    <p style={{ fontSize: '13px', margin: 0 }}>{req.admin_comment}</p>
                                                </div>
                                            )}
                                        </div>
                                    );
                                })
                            ) : (
                                <p className="empty-text">История заявок пуста</p>
                            )} */}
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default UserProfilePage;