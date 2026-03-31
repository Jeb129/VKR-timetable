export interface Building {
    id: number;
    name: string;
    address: string;
    work_start_time: string;
    work_end_time: string;
}

export interface Classroom {
    id: number;
    num: string;
    name: string;
    building: number;
    building_details?: Building; 
    work_start: string; 
    work_end: string;    
    capacity: number;
}