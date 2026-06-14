import { GenerationStatus } from "@/types/schedule";

// Вспомогательный мини-компонент для бейджа
const StatusBadge: React.FC<{ status?: GenerationStatus | null }> = ({ status }) => {
    const config = {
        [GenerationStatus.SUCCESS]: { label: 'Готово', class: 'btn-green' },
        [GenerationStatus.IN_PROGRESS]: { label: 'В процессе', class: 'btn-primary' },
        [GenerationStatus.ERROR]: { label: 'Ошибка', class: 'btn-red' },
        [GenerationStatus.INFEASIBLE]: { label: 'Нерешаемо', class: 'btn-orange' },
    };

    if (status === null || status === undefined) return <span className="badge btn-outline">Новый</span>;
    const s = config[status];
    return <span className={`badge ${s.class}`}>{s.label}</span>;
}

export default StatusBadge