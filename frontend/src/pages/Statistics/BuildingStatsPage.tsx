import { useState, useEffect } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { dbService } from "@/services/crud";
import { useModal } from "@/context/ModalContext";
import "@/styles/Stats.css";

const DAYS_SHORT = ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб"];

const BuildingStatsPage = () => {
    const { buildingId } = useParams();
    const navigate = useNavigate();
    const { openModal, closeModal } = useModal(); 
    
    const [data, setData] = useState<any>(null);
    const [loading, setLoading] = useState(true);

    const fetchRooms = async () => {
        const res = await dbService.list("statistics/load", { building_id: buildingId });
        setData(res);
        setLoading(false);
    };

    useEffect(() => { fetchRooms(); }, [buildingId]);
    const showRoomDetails = async (roomId: number) => {
        const details = await dbService.list("statistics/load", { classroom_id: roomId });
        
        // Вызываем модалку через хук
        openModal({
            title: `Аналитика: Аудитория ${details.num}`,
            width: '800px',
            content: (
                <div className="flex-col gap-3">
                    {/* Графики (код из прошлого ответа) */}
                    <div className="flex-col">
                        <h4 className="mb-2">Загрузка по парам (цикл)</h4>
                        <div className="flex-row gap-2">
                            {[1, 2].map(week => (
                                <div key={week} className="flex-col f-1 p-1 bg-main rounded-md">
                                    <div className="week-title-mini text-center">{week === 1 ? 'ЧИСЛИТЕЛЬ' : 'ЗНАМЕНАТЕЛЬ'}</div>
                                    <div className="daily-chart-container">
                                        {DAYS_SHORT.map((name, i) => {
                                            const count = details.daily_load[week][i + 1] || 0;
                                            const height = (count / details.max_pairs) * 100;
                                            return (
                                                <div key={i} className="day-column">
                                                    <div className="vertical-bar-bg" title={`${count} пар`}>
                                                        <div className="vertical-bar-fill" style={{ height: `${height}%`, backgroundColor: week === 2 ? 'var(--p-orange)' : 'var(--p-blue)' }} />
                                                    </div>
                                                    <span className="day-label">{name}</span>
                                                </div>
                                            );
                                        })}
                                    </div>
                                </div>
                            ))}
                        </div>
                    </div>

                    {/* Бронирования */}
                    <div className="flex-col gap-1">
                        <h4>Активные бронирования ({details.booking_count}):</h4>
                        <div className="scroll-y" style={{ maxHeight: '200px' }}>
                            {details.bookings.map((b: any, i: number) => (
                                <div key={i} className="p-2 border-bottom bg-white flex-row space-between">
                                    <div>
                                        <div style={{fontWeight: 700}}>{b.date}</div>
                                        <div style={{fontSize: '12px'}}>{b.reason}</div>
                                    </div>
                                    <div style={{fontWeight: 800}}>{b.time}</div>
                                </div>
                            ))}
                        </div>
                    </div>
                </div>
            ),
            footer: (
                <button className="btn btn-primary w-100" onClick={closeModal}>Закрыть</button>
            )
        });
    };

    if (loading) return <div className="p-4">Загрузка...</div>;

    return (
        <div className="flex-col bg-main min-h-screen">
            <nav className="navbar">
                <div className="logo-white" onClick={() => navigate("/")}>КГУ • СТАТИСТИКА</div>
                <button className="btn nav-btn" onClick={() => navigate("/Statistics")}>Назад</button>
            </nav>

            <div className="profile-wrapper flex-col gap-3">
                <h2 className="text-primary">{data?.building_name}</h2>
                <div className="stats-grid slide-up">
                    {data?.classrooms.map((room: any) => (
                        <div key={room.id} className="card clickable-card" onClick={() => showRoomDetails(room.id)}>
                            <div className="flex-row space-between align-center mb-1">
                                <h3>{room.num}</h3>
                                <span className="text-primary" style={{fontWeight: 800}}>{room.load_percent}%</span>
                            </div>
                            <div className="progress-wrapper">
                                <div className="progress-fill" style={{ width: `${room.load_percent}%`, backgroundColor: 'var(--p-blue)' }} />
                            </div>
                            <p className="text-muted mt-1" style={{fontSize: '0.8rem'}}>
                                Нагрузка: <b>{room.actual_hours}ч.</b> / {room.max_hours}ч.
                            </p>
                        </div>
                    ))}
                </div>
            </div>
        </div>
    );
};
export default BuildingStatsPage;