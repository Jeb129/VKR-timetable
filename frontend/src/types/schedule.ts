export interface MappedEvent {
    start: string;  // ISO дата-время
    end: string;    // ISO дата-время
    title: string;  
    type: string;   // "0", "2", "3"
    extendedProps: {
        event: {
            id: number;
            order: number;           // Номер пары
            day: number;   
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
export interface Timeslot {
    id: number;
    day: number;          // Дни (пн, вт, ср, чт, пт, сб)
    week_num: number;     // Четность
    order_number: number; // Номер пары ( слота)
    time_start: string;
    time_end: string;
}

export interface DayInfo {
    id: number;
    name: string;
}

export const DAYS = [
    { id: 1, name: "Понедельник" },
    { id: 2, name: "Вторник" },
    { id: 3, name: "Среда" },
    { id: 4, name: "Четверг" },
    { id: 5, name: "Пятница" },
    { id: 6, name: "Суббота" }
] as const;

export interface Lesson {
    id: number;
    discipline_name: string;
    type_name: string;
    classroom_name: string;
    timeslot: number;
    week_num: number;
    start: string;
    end: string;
    order: number;
    day: number;
    teacher_list: string[];
    groups_list: string[];
}
export interface ScheduleEvent {
    id: string;
    title: string;
    start: string;
    end: string;
    extendedProps: {
        lessonId: number;
        type: string;
        teacherId?: number;
        groupId?: number;
        classroomId: number;
    };
    // Настройки для FullCalendar
    editable?: boolean; 
    backgroundColor?: string;
}

export interface ConstraintError {
    name: string;
    penalty: number;
    message: string;
    data: any
}