import { publicApi, privateApi } from "@/services/axios";
import { clearTokens, getRefreshToken, setTokens } from "./tokens";
import type { RegisterRequest, LoginRequest, AuthResponse, User } from "@/types/user";

const login = async (data: LoginRequest): Promise<void> => {
  const response = await publicApi.post<AuthResponse>("/auth/login/", data)
  setTokens(
    response.data.access,
    response.data.refresh
  )
}

const register = async (data: RegisterRequest): Promise<User> => {
  const response = await publicApi.post<AuthResponse>("/auth/register/", data)
  setTokens(
    response.data.access,
    response.data.refresh
  )
  return response.data.user!
}

const logout = async () => {
  await privateApi.post("/auth/logout/")
}

const getCurrentUser  = async (): Promise<User> => {
  return (await privateApi.get("auth/me/")).data
}

export const authService = {
  login,
  register,
  logout,
  getCurrentUser
}