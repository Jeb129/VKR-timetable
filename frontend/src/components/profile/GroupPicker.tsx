import { useState} from "react";
import SearchSelect from "@/components/UI/SearchSelect";
import { privateApi } from "@/services/axios";

interface Props {
    onSuccess: () => void;
    onClose: () => void;
}

const GroupPicker = ({ onSuccess, onClose }: Props) => {
    const [selectedId, setSelectedId] = useState<number | null >(null);
    const [loading, setLoading] = useState(false);

    const handleSave = async () => {
        if (!selectedId) return;
        setLoading(true);
        try {
            // Отправляем ID выбранной группы на бэкенд
            await privateApi.patch("/auth/link-group/", { study_group_id: selectedId });
            onSuccess();
        } catch {
            alert("Ошибка при сохранении группы");
        } finally {
            setLoading(false);
        }
    };
    return (
        <div className="flex-col gap-2">
            <div className="flex-col">
                <label className="filter-label">Ваша учебная группа</label>
                <SearchSelect 
                    model="groups"
                    onChange={setSelectedId}
                    placeholder="Начните вводить шифр (напр. 24-ИС...)"
                />
            </div>
            
            <div className="flex-row gap-2 mt-2">
                <button 
                    className="btn btn-green f-1" 
                    onClick={void handleSave} 
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