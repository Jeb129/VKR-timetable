import type { SimpleEntity } from "./ui";

export interface User {
    id: number;
    username: string;
    email: string;
    is_staff: boolean;
    is_internal: boolean;       
    is_moodle_linked: boolean;   
    teacher: SimpleEntity | null;        
    study_group: SimpleEntity | null;     
    is_email_verified: boolean;
    is_schedule_moderator: boolean;
    is_booking_moderator: boolean;
}
export interface RegisterRequest {
    username: string,
    email: string,
    password: string
}

export interface LoginRequest {
    email: string,
    password: string
}