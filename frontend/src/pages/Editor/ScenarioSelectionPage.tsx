import React, { useState, useEffect, useCallback } from "react";
import { useNavigate } from "react-router-dom";
import { dbService } from "@/services/crud";
import { scenarioService } from "@/services/scenarioService";
import { useModal } from "@/context/ModalContext";
import type { Scenario } from "@/types/schedule";
import SearchSelect from "@/components/UI/SearchSelect";
import "@/styles/ScenarioSelection.css";

const ScenarioSelectionPage: React.FC = () => {
    const navigate = useNavigate();
    const { openModal, closeModal } = useModal();
    const [scenarios, setScenarios] = useState<Scenario[]>([]);
    const [loading, setLoading] = useState(true);

    const fetchScenarios = useCallback(async () => {
        setLoading(true);
        try {
            const data = await dbService.list<Scenario>('scenarios');
            setScenarios(data.results);
        } catch (err) {
            console.error("Ошибка загрузки", err);
        } finally {
            setLoading(false);
        }
    }, []);

    useEffect(() => { fetchScenarios(); }, [fetchScenarios]);

    const openCreateModal = () => {
        let name = "";
        let semId: number | null = null;
        openModal({
            title: "Новая версия расписания",
            content: (
                <div className="flex-col gap-2">
                    <div className="flex-col">
                        <label className="filter-label">Название</label>
                        <input className="input-styled" placeholder="Напр: Осенний семестр 2024" onChange={e => name = e.target.value} />
                    </div>
                    <div className="flex-col">
                        <label className="filter-label">Семестр</label>
                        <SearchSelect model="semesters" placeholder="Выберите семестр..." onChange={val => semId = Number(val)} />
                    </div>
                </div>
            ),
            footer: (
                <div className="flex-row gap-2 w-100">
                    <button className="btn btn-green f-1" onClick={async () => {
                        await dbService.create('scenarios', { name, semester: semId });
                        closeModal();
                        fetchScenarios();
                    }}>Создать</button>
                    <button className="btn btn-outline f-1" onClick={closeModal}>Отмена</button>
                </div>
            )
        });
    };

    return (
        <div className="flex-col bg-main min-h-screen">
            <nav className="navbar">
                <div className="logo-white" onClick={() => navigate("/")} style={{cursor:'pointer'}}>КГУ • РАСПИСАНИЕ</div>
                <button className="btn nav-btn" onClick={() => navigate("/profile")}>В профиль</button>
            </nav>

            <div className="profile-wrapper flex-col gap-3 w-100">
                {/* Заголовок слева, кнопка справа */}
                <div className="flex-row space-between align-center w-100">
                    <h2 className="text-primary">Варианты расписания</h2>
                    <button className="btn btn-primary" onClick={openCreateModal}>Создать версию</button>
                </div>

                <div className="scenario-grid slide-up">
                    {loading ? <div className="card text-center f-1">Загрузка...</div> : 
                    scenarios.map(s => (
                        <div key={s.id} className="card scenario-card">
                            <div className="flex-col gap-1">
                                <div className="flex-row space-between align-start">
                                    <h3 className="text-primary">{s.name}</h3>
                                    <span className={`badge ${s.is_active ? 'btn-green' : 'btn-outline'}`}>
                                        {s.is_active ? 'Активен' : 'Черновик'}
                                    </span>
                                </div>
                                <span className="text-muted small">Дата создания: {new Date(s.created_at).toLocaleDateString()}</span>
                            </div>

                            <div className="card-actions flex-col mt-2">
                                {/* ГЛАВНЫЙ ПЕРЕХОД ТЕПЕРЬ В ГЕНЕРАТОР (ScenarioPage) */}
                                <button 
                                    className="btn btn-primary w-100" 
                                    onClick={() => navigate(`/scenarios/${s.id}`)}
                                >
                                    Управление и Генерация
                                </button>
                                <div className="flex-row gap-1">
                                    <button className="btn btn-orange f-1" onClick={() => scenarioService.copy(s.id).then(fetchScenarios)}>Копировать</button>
                                    <button className="btn btn-red f-1" onClick={() => dbService.remove('scenarios', s.id).then(fetchScenarios)}>Удалить</button>
                                </div>
                            </div>
                        </div>
                    ))}
                </div>
            </div>
        </div>
    );
};

export default ScenarioSelectionPage;