import React, { useState, useEffect, useCallback } from "react";
import { useNavigate } from "react-router-dom";
import { dbService } from "@/services/crud";
import { useModal } from "@/context/ModalContext";
import type { Scenario } from "@/types/schedule";
import "@/styles/ScenarioSelection.css";
import SearchSelect from "@/components/UI/SearchSelect";
import { scenarioService } from "@/services/scenarioService";

const ScenarioSelectionPage: React.FC = () => {
    const navigate = useNavigate();
    const { openModal, closeModal } = useModal();
    const [scenarios, setScenarios] = useState<Scenario[]>([]);
    const [loading, setLoading] = useState(true);

    const fetchScenarios = useCallback(async () => {
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

    const handleCreate = async (name: string, semesterId: number) => {
        await dbService.create('scenarios', { name, semester: semesterId });
        closeModal();
        fetchScenarios();
    };

    const openCreateModal = () => {
        let name = "";
        let semId: number | null = null;
        openModal({
            title: "Создать новый вариант",
            content: (
                <div className="flex-col gap-2">
                    <input className="input-styled" placeholder="Название..." onChange={e => name = e.target.value} />
                    <SearchSelect model="semesters" placeholder="Выберите семестр..." onChange={val => semId = val} />
                </div>
            ),
            footer: (
                <div className="flex-row gap-2 justify-end">
                    <button className="btn btn-outline" onClick={closeModal}>Отмена</button>
                    <button className="btn btn-primary" onClick={() => handleCreate(name, semId!)}>Создать</button>
                </div>
            )
        });
    };

    return (
        <div className="flex-col min-h-screen">
            <nav className="navbar">
                <h3 onClick={() => navigate("/")} style={{cursor:'pointer'}}>КГУ • Расписание</h3>
            </nav>

            <div className="p-3 flex-col gap-3">
                <div className="flex-row space-between align-center">
                    <h1>Варианты расписания</h1>
                    <button className="btn btn-primary" onClick={openCreateModal}>+ Создать</button>
                </div>

                <div className="scenario-grid">
                    {scenarios.map(s => (
                        <div key={s.id} className="card scenario-card">
                            <div className="flex-col gap-1">
                                <div className="flex-row space-between">
                                    <h3 className="text-primary">{s.name}</h3>
                                    <span className={`badge ${s.is_active ? 'btn-green' : 'btn-outline'}`}>
                                        {s.is_active ? 'Активен' : 'Черновик'}
                                    </span>
                                </div>
                                <span className="text-muted">Дата: {new Date(s.created_at).toLocaleDateString()}</span>
                            </div>
                            <div className="card-actions">
                                <button className="btn btn-primary f-1" onClick={() => navigate(`/scenarios/${s.id}`)}>Открыть</button>
                                <button className="btn btn-outline" onClick={() => scenarioService.copy(s.id).then(fetchScenarios)}>📋</button>
                                <button className="btn btn-outline" onClick={() => dbService.remove('scenarios', s.id).then(fetchScenarios)}>🗑</button>
                            </div>
                        </div>
                    ))}
                </div>
            </div>
        </div>
    );
};

export default ScenarioSelectionPage;