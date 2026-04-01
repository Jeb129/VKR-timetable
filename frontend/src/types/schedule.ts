export interface MappedEvent {
    type: 'lesson' | 'adjustment' | 'booking';
    date_start: string; // ISO string
    date_end: string;   // ISO string
    event: {
        id: number;
        discipline_name?: string;
        type_name?: string;
        classroom_name?: string;
        teachers_list?: string[];
        groups_list?: string[];
        description?: string; // для броней
        user_name?: string;    // для броней
    };
}
export interface Lesson {
    id: number;
    discipline_name: string;
    type_name: string;
    classroom_name: string;
    start: string;
    end: string;
    order: number;
    day: number;
    teacher_list: string[];
    groups_list: string[];
}