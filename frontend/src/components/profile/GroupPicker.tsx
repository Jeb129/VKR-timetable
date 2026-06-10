import { useState, useEffect } from "react";
import { dbService } from "@/services/crud";
import SearchSelect from "@/components/UI/SearchSelect";
import { privateApi } from "@/services/axios";
import type { SelectOption } from "@/types/ui";

interface Props {
    onSuccess: () => void;
    onClose: () => void;
}

const GroupPicker = ({ onSuccess, onClose }: Props) => {
    const [groups, setGroups] = useState<any[]>([]);
    const [selectedId, setSelectedId] = useState<string | number>("");
    const [loading, setLoading] = useState(false);
    const [fetching, setFetching] = useState(true);

    useEffect(() => {
        const fetchGroups = async () => {
            try {
                const data = await dbService.list("groups");
                const list = Array.isArray(data) ? data : data.results || [];
                setGroups(list);
            } catch (e) {
                console.error("Ошибка загрузки групп:", e);
            } finally {
                setFetching(false);
            }
        };
        fetchGroups();
    }, []);

    const handleSave = async () => {
        if (!selectedId) return;
        setLoading(true);
        try {
            await privateApi.patch("/auth/link-group/", { study_group_id: selectedId });
            onSuccess();
        } catch (e) {
            alert("Ошибка при сохранении группы");
        } finally {
            setLoading(false);
        }
    };

    // Формируем опции для поиска по ВСЕМ группам сразу
    const options: SelectOption[] = groups.map(g => ({
        value: g.id,
        label: g.name 
    }));

    return (
        <div className="flex-col gap-2">
            <div className="flex-col">
                <label className="filter-label">Ваша учебная группа</label>
                <SearchSelect 
                    options={options}
                    value={selectedId}
                    onChange={setSelectedId}
                    placeholder={fetching ? "Загрузка списка..." : "Начните вводить шифр (напр. 24-ИС...)"}
                />
            </div>
            
            <p className="text-muted" style={{ fontSize: '12px' }}>
                Введите номер или направление, чтобы быстро найти свою группу в списке.
            </p>

            <div className="flex-row gap-2 mt-2">
                <button 
                    className="btn btn-green f-1" 
                    onClick={handleSave} 
                    disabled={loading || !selectedId}
                >
                    {loading ? "Сохранение..." : "Привязать профиль"}
                </button>
                <button className="btn btn-outline f-1" onClick={onClose}>Отмена</button>
            </div>
        </div>
    );
};

export default GroupPicker;