import { useState } from "react"
import { Navigate, useNavigate } from "react-router-dom"
import type { LoginRequest } from "@/types/user"
import { useAuth } from "@/context/AuthContext"

const LoginPage = () => {
  const { isAuthenticated, isLoading, login } = useAuth()
  const redirectPath = localStorage.getItem("redirectAfterLogin")
  // Если пользователь уже авторизован - перенаправляем
  if (!isLoading && isAuthenticated) {
    return <Navigate to="/profile" replace />
  }

  const [loginError, setLoginError] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)
  const [showPassword, setShowPassword] = useState(false)

  const navigate = useNavigate()
  const [form, setForm] = useState<LoginRequest>({
    email: "",
    password: "",
  })

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target
    setForm((prev) => ({ ...prev, [name]: value }))
  }

  const handleSubmit = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault()
    setLoginError(null)

    try {
      setLoading(true)
      await login(form)
      if (redirectPath) {
        localStorage.removeItem("redirectAfterLogin")
        navigate(redirectPath)
      } else {
        navigate("/profile")
      }
    } catch (err: any) {
      setLoginError(err?.response?.data?.detail ?? "Вход не выполнен")
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="flex-row justify-center flex-grow">
      <div className="flex-col justify-center gap-2">
        <div className="flex-col slide-up gap-1 card max-width">
          <div className="justify-center">
            <h1 className="primary-text">Вход</h1>
          </div>
          <form
            className="flex-col gap-1"
            onSubmit={handleSubmit}
          >
            <div className="flex-col">
              <label>Email</label>
              <input
                className="focus-glow border"
                name="email"
                type="email"
                value={form.email}
                onChange={handleChange}
                required
              />
            </div>

            <div className="flex-col">
              <label>Пароль</label>
              <div className="flex-row gap-1">
                <input
                  className="focus-glow flex-grow border"
                  name="password"
                  type={showPassword ? "text" : "password"}
                  value={form.password}
                  onChange={handleChange}
                  required
                />
                <div
                  className="primary-btn"
                  onClick={() => setShowPassword((prev) => !prev)}>
                  <span>{showPassword ? "🔓" : "🔒"}</span>
                </div>
              </div>
            </div>

            {loginError && (
              <div className="error"
                onClick={() => setLoginError(null)}
              >{loginError}</div>
            )}

            <button
              className="primary-btn hover-lift transition-all"
              type="submit"
              disabled={loading}
            >
              {loading ? "Авторизация..." : "Вход"}
            </button>
          </form>
        </div>
        { redirectPath ? (<></>) : (
          <>
          <div className="flex-col fade-in card max-width">
            <div className="justify-center">
            <h3>Нет аккаунта?</h3>
          </div>
          <button
            className="transition-all secondary-btn"
            onClick={() => navigate("/register")}
          >
            Регистрация
          </button>
        </div>
          <a onClick={() => navigate("/")}>... На главную</a>
          </>       
        )}
      </div>

    </div>
  )
}
export default LoginPage