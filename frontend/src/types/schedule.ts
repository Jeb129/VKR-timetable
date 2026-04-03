export interface MappedEvent {
    start: string;  // ISO дата-время
    end: string;    // ISO дата-время
    title: string;  
    type: string;   // "0", "2", "3"
    extendedProps: {
        event: {
            id: number;
            discipline_name?: string;
            type_name?: string;
            classroom_name?: string;
            teachers_list?: string[];
            groups_list?: string[];
            description?: string;   // Для брони
            user_name?: string;     // Для брони
            status?: number;
            admin_comment?: string;
        }
    }
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