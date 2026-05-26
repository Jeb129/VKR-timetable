export interface MappedEvent {
    start: string;  // ISO дата-время
    end: string;    // ISO дата-время
    title: string;  
    type: string;   // "0", "2", "3"
    extendedProps: {
        event: {
             id: number;
            discipline: string;     // Название дисциплины (строка)
            lesson_type: string;    // Тип занятия (строка)
            classroom: string;       // Название аудитории (строка)
            teachers: SimpleEntity[]; // Массив объектов {id, name}
            study_groups: SimpleEntity[]; // Массив объектов {id, name}
            
            // Поля для бронирований
            description?: string;
            user_name?: string;
            status?: number;
            admin_comment?: string;
            
            // Системные поля для фильтрации
            order: number;
            day: number;
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

export interface ScheduleScenario {
    id: number;
    name: string;
    is_active: boolean;
    created_at: string;
    semester?: number;
}

export interface Scenario {
    id: number;
    name: string;
    is_active: boolean;
    created_at: string;
    semester?: number;
}

export interface SimpleEntity {
    id: number;
    name: string;
}

export interface DraftChange {
    field: string;
    was: SimpleEntity | SimpleEntity[] | null;
    now: SimpleEntity | SimpleEntity[] | null;
}

export interface Lesson {
    id: string;
    scenario: number;

    discipline: string;
    lesson_type: string;
    classroom: string;
    timeslot: Timeslot;

    teachers: SimpleEntity[];
    study_groups: SimpleEntity[];

    whole_weeks: number;
    draft_info: {is_new: boolean; changes: DraftChange[]} | null
}