import { useState, useEffect } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { dbService } from "@/services/crud";
import Modal from "@/components/UI/Modal";
import "@/styles/Stats.css";

const BuildingStatsPage = () => {
    const { buildingId } = useParams();
    const navigate = useNavigate();
    const [data, setData] = useState<any>(null);
    const [roomDetails, setRoomDetails] = useState<any>(null); 

    const fetchRooms = async () => {
        const res = await dbService.list("statistics/load", { building_id: buildingId });
        setData(res);
    };

    useEffect(() => { fetchRooms(); }, [buildingId]);

    const openRoomInfo = async (roomId: number) => {
        const res = await dbService.list("statistics/load", { classroom_id: roomId });
        setRoomDetails(res);
    };

    return (
        <div className="flex-col bg-main min-h-screen">
            <nav className="navbar">
                <div className="logo-white" onClick={() => navigate("/")}>КГУ • СТАТИСТИКА</div>
                <button className="btn nav-btn" onClick={() => navigate("/Statistics")}>Назад</button>
            </nav>

            <div className="profile-wrapper flex-col gap-3">
                <h2 className="text-primary">{data?.building_name}</h2>
                
                {/* Сетка аудиторий */}
                <div className="stats-grid slide-up">
                    {data?.classrooms.map((room: any) => (
                        <div key={room.id} className="card clickable-card" onClick={() => openRoomInfo(room.id)}>
                            <div className="flex-row space-between align-center mb-1">
                                <h3>{room.num}</h3>
                                <span className="text-primary" style={{fontWeight: 800}}>{room.load_percent}%</span>
                            </div>
                            <div className="progress-wrapper">
                                <div className="progress-fill" style={{ width: `${room.load_percent}%`, backgroundColor: 'var(--p-blue)' }} />
                            </div>
                            <p className="text-muted" style={{fontSize: '0.8rem'}}>
                                Нагрузка: {room.actual_hours} ч. / {room.max_hours} ч.
                            </p>
                        </div>
                    ))}
                </div>
            </div>

            {/* НОВАЯ МОДАЛКА С ДЕТАЛЯМИ БРОНИРОВАНИЯ */}
            <Modal 
                isOpen={!!roomDetails} 
                onClose={() => setRoomDetails(null)}
                title={`Аудитория ${roomDetails?.num}`}
            >
                <div className="flex-col gap-2">
                    <div className="flex-row space-between p-2 bg-main rounded-md">
                        <strong>Всего активных броней:</strong>
                        <span className="badge btn-orange">{roomDetails?.booking_count}</span>
                    </div>

                    <div className="flex-col gap-1 mt-1">
                        <h4>Список бронирований:</h4>
                        <div className="scroll-y" style={{maxHeight: '300px'}}>
                            {roomDetails?.bookings.length > 0 ? roomDetails.bookings.map((b: any, i: number) => (
                                <div key={i} className="p-2 border-bottom mb-1 bg-white card" style={{borderWidth: '1px'}}>
                                    <div className="flex-row space-between">
                                        <span className="text-primary" style={{fontWeight: 700}}>{b.date}</span>
                                        <span className="text-muted">{b.time}</span>
                                    </div>
                                    <p className="mt-1" style={{fontSize: '14px'}}><strong>Причина:</strong> {b.reason}</p>
                                    <small className="text-muted">Ответственный: {b.user}</small>
                                </div>
                            )) : <p className="text-center p-3 text-muted">Бронирований не найдено</p>}
                        </div>
                    </div>
                </div>
            </Modal>
        </div>
    );
};

export default BuildingStatsPage;