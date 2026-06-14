import { GenerationStatus } from "@/types/schedule";

// Вспомогательный мини-компонент для бейджа
const StatusBadge: React.FC<{ status?: {id:GenerationStatus; name: string} | null}> = ({ status }) => {
    const config = {
        [GenerationStatus.SUCCESS]: { class: 'btn-green' },
        [GenerationStatus.IN_PROGRESS]: { class: 'btn-primary' },
        [GenerationStatus.ERROR]: { class: 'btn-red' },
        [GenerationStatus.INFEASIBLE]: {class: 'btn-orange' },
        [GenerationStatus.IN_QUERRY]: { class: 'btn-orange' },
    };

    if (status === null || status === undefined) return <span className="badge btn-outline">Новый</span>;
    const s = config[status.id];
    return <span className={`badge ${s.class}`}>{status.name}</span>;
}

export default StatusBadge