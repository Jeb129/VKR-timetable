import { publicApi, privateApi } from "@/services/axios";
import type { RegisterRequest, LoginRequest, User } from "@/types/user";

const login = async (data: LoginRequest): Promise<void> => {
  const response = await publicApi.post("/auth/login/", data)
  return response.data
}

const register = async (data: RegisterRequest): Promise<User> => {
  const response = await publicApi.post<User>("/auth/register/", data)
  return response.data
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