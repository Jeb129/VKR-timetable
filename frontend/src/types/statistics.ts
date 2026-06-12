export interface BuildingStat {
    id: number;
    short_name: string;
    name: string;
    load_percent: number;
    rooms_count: number;
}

export interface ClassroomStat {
    id: number;
    num: string;
    name: string;
    load_percent: number;
    lessons_count: number;
    capacity: number;
}