import { createContext, useContext, useEffect, useState,} from "react"
import { authService } from "@/services/auth/auth"

import type { ReactNode } from "react"
import type { LoginRequest, User } from "@/types/user"
import type { RegisterRequest } from "@/types/user"
import { dbService } from "@/services/crud"

// Контекст в котором хранится пользователь если авторизован
// Используется через хук useAuth (экспорт ниже)
export interface AuthContextType {
  user: User | null
  isAuthenticated: boolean
  isLoading: boolean

  login: (data: LoginRequest) => Promise<void>
  register: (data: RegisterRequest) => Promise<void>
  logout: () => Promise<void>
  refreshUser: () => Promise<void>
  updateUser: (data: Record<string,string>) => Promise<void>
}

const AuthContext = createContext<AuthContextType | undefined>(undefined)

interface AuthProviderProps {
  children: ReactNode
}

const AuthProvider = ({ children }: AuthProviderProps) => {
  const [user, setUser] = useState<User | null>(null)
  const [isLoading, setIsLoading] = useState<boolean>(true)

  const isAuthenticated = !!user

  const updateUser = async (data: Record<string,string>) => {
    if (!user) return
    const updated = await dbService.update("user",user.id,data)
    if (updated) setUser(updated)
  }

  const refreshUser = async () => {
    const u = await authService.getCurrentUser()
    setUser(u)
  }

  const login = async (data: LoginRequest) => {
    await authService.login(data)
    refreshUser()
  }

  const register = async (data: RegisterRequest) => {
    const u = await authService.register(data)
    setUser(u)
  }

  const logout = async () => {
    try {
      await authService.logout()
    } finally {
      setUser(null)
    }
  }

  useEffect(() => {
    const init = async () => {
      try {
        await refreshUser()
      } catch {
        setUser(null)
      } finally {
        setIsLoading(false)
      }
    }

    init()
  }, [])

  const value: AuthContextType = {
    user,
    isAuthenticated,
    isLoading,
    login,
    register,
    logout,
    refreshUser,
    updateUser
  }

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

export const useAuth = (): AuthContextType => {
  const context = useContext(AuthContext)

  if (!context) {
    throw new Error("useAuth must be used inside AuthProvider")
  }

  return context
}
export default AuthProvider