import axios from "axios"
import type { AxiosError, InternalAxiosRequestConfig } from "axios"

import { getAccessToken, getRefreshToken, setTokens, clearTokens } from "@/services/auth/tokens"
import type { AuthResponse } from "@/types/user"

const BASE_URL = import.meta.env.VITE_API_URL ?? "http://localhost:8000"


// Работа с токенами

// Public client
export const publicApi = axios.create({
  baseURL: BASE_URL,
})

// Private client
export const privateApi = axios.create({
  baseURL: BASE_URL,
})
// добавляем Access токен в заголовок
privateApi.interceptors.request.use(
  (config: InternalAxiosRequestConfig) => {
    const token = getAccessToken()
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  }
)
// При ошмбке 401 пробуем обновить токены
privateApi.interceptors.response.use(
  (response) => response,
  async (error: AxiosError) => {
    const originalRequest = error.config as InternalAxiosRequestConfig & {
      _retry?: boolean
      // При добавлении флага он по умолчанию становится undefined
    }
    console.debug("privateApi Ошибка\n", error.message)

    // если ошибка 401 и это не повторный запрос
    if (error.response?.status === 401 && originalRequest._retry === undefined) {
      originalRequest._retry = true
      try {

        // Запрашиваем новые токены
        const refreshToken = getRefreshToken()
        if (!refreshToken) {
          throw error
        }
        const response = await publicApi.post<AuthResponse>(
          "/auth/refresh",
          { refresh_token: refreshToken }
        )
        const tokens = response.data

        if (!tokens) {
          throw error
        }
        setTokens(tokens.access, tokens.refresh)
        // Обновляем acess в заголовоке
        originalRequest.headers.Authorization = `Bearer ${tokens.access}`
        // Отправляем оригинальный запрос повторно
        return privateApi(originalRequest)
      } catch (refreshError) {
        throw refreshError
      }
    }
    // если обновление токенов не удалось - перебрасываем на login
    if (error.response?.status === 401) {

      clearTokens()

      localStorage.setItem(
        "redirectAfterLogin",
        window.location.pathname + window.location.search
      )

      window.location.href = "/login"
    }

    return Promise.reject(error)
  }
)
