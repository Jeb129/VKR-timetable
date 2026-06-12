import { useState } from "react";
import { useAuth } from "@/context/AuthContext";
import AsyncSearchSelect from "@/components/UI/SearchSelect"; 
import { privateApi } from "@/services/axios";

interface Props {
    onSuccess: () => void;
    onClose: () => void;
}

const GroupPicker = ({ onSuccess, onClose }: Props) => {
    const [selectedId, setSelectedId] = useState<number | null>(null);
    const [loading, setLoading] = useState(false);

    const handleSave = async () => {
        if (!selectedId) return;
        setLoading(true);
        try {
            // Отправляем ID выбранной группы на бэкенд
            await privateApi.patch("/auth/link-group/", { study_group_id: selectedId });
            onSuccess();
        } catch (e) {
            console.error("Ошибка при сохранении группы", e);
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="flex-col gap-2">
            <div className="flex-col">
                <label className="filter-label">Ваша учебная группа</label>
                <AsyncSearchSelect 
                    model="groups" 
                    value={selectedId}
                    onChange={(val) => setSelectedId(val)}
                    placeholder="Введите шифр группы (напр. 22-ИС...)"
                    isMulti={false}
                />
            </div>
            
            <div className="flex-row gap-2 mt-2">
                <button 
                    className="btn btn-green f-1" 
                    onClick={handleSave} 
                    disabled={loading || !selectedId}
                >
                    {loading ? "Связывание..." : "Привязать профиль"}
                </button>
                <button className="btn btn-outline f-1" onClick={onClose}>Отмена</button>
            </div>
        </div>
    );
};

export default GroupPicker;