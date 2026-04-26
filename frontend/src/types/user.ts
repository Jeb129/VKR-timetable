export interface User {
    id: number,
    username: string,
    email: string,
    is_staff: boolean,
    internal_user: boolean; 
    moodle_id?: number | null;
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

export interface AuthResponse {
    user?: User
    access: string,
    refresh: string,
}