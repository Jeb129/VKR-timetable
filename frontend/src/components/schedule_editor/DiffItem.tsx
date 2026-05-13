// components/schedule_editor/DiffViewer.tsx
import { type SimpleEntity } from "@/types/schedule";

interface DiffItemProps {
    value: SimpleEntity | SimpleEntity[] | null;
    className?: string;
}

export const DiffItem = ({ value, className = "" }: DiffItemProps) => {
    if (!value) return <span className={className}>—</span>;

    // Если это массив (M2M)
    if (Array.isArray(value)) {
        return (
            <div className={`flex-row flex-wrap gap-1 ${className}`}>
                {value.map((item, idx) => (
                    <span key={item.id} className="diff-entity-tag">
                        {item.name}{idx < value.length - 1 ? "," : ""}
                    </span>
                ))}
            </div>
        );
    }

    // Если это одиночный объект (FK)
    return <span className={`font-bold ${className}`}>{value.name}</span>;
};