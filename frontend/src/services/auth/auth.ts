import { publicApi, privateApi } from "@/services/axios";
import { clearTokens, getRefreshToken, setTokens } from "./tokens";
import type { RegisterRequest, LoginRequest, AuthResponse, User } from "@/types/user";

const login = async (data: LoginRequest): Promise<User | undefined> => {
  const response = await publicApi.post<AuthResponse>("/auth/login", data)
  setTokens(
    response.data.access,
    response.data.refresh
  )
  return response.data?.user
}

const register = async (data: RegisterRequest): Promise<User> => {
  const response = await publicApi.post<AuthResponse>("/auth/register", data)
  setTokens(
    response.data.access,
    response.data.refresh
  )
  return response.data.user!
}

const logout = async () => {
  const refresh_token = getRefreshToken()
  clearTokens() // Фронтенд разлогинивается вне зависимости от сервера
  await privateApi.post("/auth/logout", { refresh: refresh_token })
}

const getCurrentUserId  = async () => {
  return (await privateApi.get("auth/verify")).data
}

export const authService = {
  login,
  register,
  logout,
  getCurrentUserId
}