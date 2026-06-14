import type { SimpleEntity } from "./ui";

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
            lesson_name?: string;    // Название дисциплины для Adjustment
            classroom: string;       // Название аудитории (строка)
            teachers: SimpleEntity[]; // Массив объектов {id, name}
            study_groups: SimpleEntity[]; // Массив объектов {id, name}
            
            // Поля для бронирований
            description?: string;
            classroom_name?: string;
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

    start: string; 
    end: string;

    whole_weeks: number;
    draft_info: {is_new: boolean; changes: DraftChange[]} | null
}

export enum GenerationStatus {
    SUCCESS = 0,
    IN_PROGRESS = 1,
    ERROR = 2,
    INFEASIBLE = 3
}

export interface Constraint {
    id: number;
    name: string; // Имя метода в коде
    description: string;
    weight: number;
    is_active: boolean;
    is_hard: boolean;
    manual_only: boolean;
    generation_only: boolean;
}

export interface Scenario {
    id: number;
    name: string;
    semester: number; // ID семестра
    semester_name?: string; // Если бэк присылает через SerializerMethodField
    is_active: boolean;
    generation_status: GenerationStatus | null;
    total_penalty: number;
    created_at: string;
}

export interface PlannedCheckResult {
    is_ok: boolean;
    missing_hours: number;
    details: {
        discipline: string;
        group: string;
        remaining: number;
    }[];
}

export type CeleryState = 
    | 'PENDING'   // Задача ожидает в очереди
    | 'STARTED'   // Задача взята воркером в работу
    | 'SUCCESS'   // Задача успешно завершена
    | 'FAILURE'   // Произошла критическая ошибка
    | 'REVOKED'   // Задача была отменена пользователем
    | 'RETRY';    // Повторная попытка

export interface GenerationStatusResponse {
    // Общее состояние для фронтенда
    // Если метаданных в кеше нет, бэк пришлет только { "state": "IDLE" }
    state: 'IDLE' | string; 

    // Данные из GenerationTaskManager (доступны, если state != 'IDLE')
    scenario_id?: number;
    semester_id?: number;
    user_id?: number;
    task_id?: string;
    start_time?: string; // ISO DateTime string
    stop_signal?: boolean; // Была ли нажата кнопка "Остановить"

    // Статус задачи из Celery (AsyncResult.state)
    celery_state?: CeleryState;

    // Статус сценария напрямую из БД (добавляется в ViewSet)
    scenario_status?: GenerationStatus; 

    // Опционально: можно добавить поля для прогресса, если добавишь их в metadata на бэке
    progress?: number; 
    current_penalty?: number;
}

/**
 * Структура записи нагрузки, которая не была распределена.
 * Основана на полях модели AcademicLoad.
 */
export interface UncoveredLoadData {
    id: number;
    discipline_name: string;      // Обычно в сериализаторах передают названия для фронтенда
    lesson_type_name: string;
    teacher_name: string;
    study_group_name: string;
    whole_hours: number;
    whole_weeks: number;
    // Можно добавить id сущностей, если нужно делать ссылки
    discipline?: number;
    teacher?: number;
    study_group?: number;
}

/**
 * Ответ от эндпоинта /plannedlessons/check/
 */
export interface PlannedCheckResult {
    status: 'ok' | 'warning';
    message: string;
    
    // Данные присутствуют только если статус 'warning'
    uncovered_data?: UncoveredLoadData[];
}