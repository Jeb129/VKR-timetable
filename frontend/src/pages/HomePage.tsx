import { useNavigate } from "react-router-dom";
import { useAuth } from "@/context/AuthContext";
import "@/styles/Profile.css"; // Используем те же отступы, что и в профиле

const HomePage = () => {
    const navigate = useNavigate();
    const { user, logout } = useAuth();

    const services = [
        {
            title: "Расписание занятий",
            desc: "Просмотр актуального расписания по аудиториям, группам и преподавателям.",
            path: "/schedule",
            color: "var(--p-blue)",
            show: true
        },
        {
            title: "Бронирование",
            desc: "Заявка на свободное время в аудиториях для проведения мероприятий.",
            path: "/Booking",
            color: "var(--p-green)",
            show: true
        },
        {
            title: "Перенос занятий",
            desc: "Инструмент для преподавателей по разовому изменению времени пары.",
            path: "/TeacherAdjustment",
            color: "var(--p-orange)",
            show: true
        },
        {
            title: "Модерация",
            desc: "Управление входящими заявками на бронирование и перенос.",
            path: "/Moderation",
            color: "var(--p-red)",
            show: true // потом заглушить админкой user?.is_staff
        },
        {
            title: "Редактор расписания",
            desc: "Управление версиями (черновиками) и основными сетками расписания.",
            path: "/ScheduleEditor",
            color: "var(--p-blue)",
            show: true
        },
        {
            title: "Импорт нагрузки",
            desc: "Загрузка учебных планов из Excel файлов в систему.",
            path: "/AcademicLoad",
            color: "var(--p-blue)",
            show: true
        }
    ];

    return (
        <div className="flex-col bg-main min-h-screen">
            <nav className="navbar">
                <div className="logo-white">КГУ • ГЛАВНАЯ</div>
                <div className="flex-row gap-10">
                    <button className="btn nav-btn" onClick={() => navigate("/profile")}>Профиль</button>
                    <button className="btn nav-btn btn-red" onClick={logout}>Выйти</button>
                </div>
            </nav>

            <div className="profile-wrapper flex-col gap-3">
                <div className="flex-col">
                    <h2 className="text-primary">Добро пожаловать, {user?.username}!</h2>
                    <p className="text-muted">Выберите необходимый сервис для работы с системой</p>
                </div>

                <div className="flex-row flex-wrap gap-2 slide-up">
                    {services.map((s, i) => s.show && (
                        <div 
                            key={i} 
                            className="card flex-col justify-center align-center text-center hover-lift" 
                            style={{ 
                                flex: '1 1 300px', 
                                minHeight: '200px', 
                                cursor: 'pointer',
                                borderColor: s.color 
                            }}
                            onClick={() => navigate(s.path)}
                        >
                            <h3 style={{ color: s.color, marginBottom: '10px' }}>{s.title}</h3>
                            <p className="text-muted" style={{ fontSize: '14px' }}>{s.desc}</p>
                        </div>
                    ))}
                </div>
            </div>
        </div>
    );
};

export default HomePage;