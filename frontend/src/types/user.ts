export interface User {
    id: number,
    username: string,
    email: string
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