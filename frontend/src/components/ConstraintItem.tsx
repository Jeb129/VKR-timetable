import type { Constraint } from "@/types/schedule";

interface ConstraintItemProps {
    constraint: Constraint;
    onUpdate: (id: number, data: Partial<Constraint>) => void;
}

const ConstraintItem: React.FC<ConstraintItemProps> = ({ constraint, onUpdate }) => {
    return (
        <div className="constraint-row flex-col gap-1 p-1">
            <div className="flex-row space-between align-center">
                <span style={{ fontSize: '0.9rem', fontWeight: 600, color: constraint.is_active ? 'var(--text-main)' : 'var(--text-muted)' }}>
                    {constraint.description}
                </span>
                <input 
                    type="checkbox" 
                    checked={constraint.is_active} 
                    onChange={(e) => onUpdate(constraint.id, { is_active: e.target.checked })}
                />
            </div>
            <div className={`flex-row align-center gap-2 ${!constraint.is_active ? 'opacity-50' : ''}`}>
                <input 
                    type="range" 
                    className="f-1" 
                    min="1" 
                    max="100" 
                    disabled={!constraint.is_active}
                    value={constraint.weight} 
                    onChange={(e) => onUpdate(constraint.id, { weight: parseInt(e.target.value) })}
                />
                <span className="text-muted" style={{ minWidth: '30px' }}>{constraint.weight}</span>
            </div>
        </div>
    );
};

export default ConstraintItem