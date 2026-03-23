import { useState } from "react"
import { Navigate, useNavigate } from "react-router-dom"
import type { RegisterRequest } from "../../types/user"
import "./Auth.css"; 
import { useAuth } from "@/context/AuthContext"

const RegisterPage = () => {

  const { isAuthenticated, isLoading, register } = useAuth()

  // Если пользователь уже авторизован - перенаправляем
  if (!isLoading && isAuthenticated) {
    return <Navigate to="/profile" replace />
  }
  
  const navigate = useNavigate()

  const [form, setForm] = useState<RegisterRequest>({
    username: "",
    email: "",
    password: "",
  })
  const [confirmPassword, setConfirmPassword] = useState("")

  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)

const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target
    setForm((prev) => ({
      ...prev,
      [name]: value,
    }))
  }

  const handleSubmit = async (
    e: React.FormEvent<HTMLFormElement>
  ) => {
    e.preventDefault()
    setError(null)

    if (form.password !== confirmPassword) {
      setError("Пароли не совпадают")
      return
    }

    try {
      setLoading(true)

      await register(form)
      
       navigate("/profile")
    } catch (err: any) {
      setError(err?.response?.data?.detail || "Не удалось зарегистрироваться")
    } finally {
      setLoading(false)
    }
  }
  return (
    <div className="flex-row justify-center flex-grow">
      <div className="flex-col justify-center gap-10">
        <div className="flex-col card slide-up" style={{width: 400}} >
          <div className="justify-center">
            <h2>Регистрация</h2>
          </div>
          <form className="flex-col gap-20" onSubmit={handleSubmit}>
            <div className="flex-col">
              <label>Имя</label>
              <input
                className="focus-glow"
                name="username"
                value={form.username}
                onChange={handleChange}
                required
              />
            </div>
            <div className="flex-col">
              <label>Email</label>
              <input
                className="focus-glow"
                name="email"
                type="email"
                value={form.email}
                onChange={handleChange}
                required
              />
            </div>

            <div className="flex-col">
              <label>Пароль</label>
              <input
                className="focus-glow"
                name="password"
                value={form.password}
                onChange={handleChange}
                required
              />
            </div>

            <div className="flex-col">
              <label>Повтор пароля</label>
              <input
                className="focus-glow"
                type="password"
                value={confirmPassword}
                onChange={(e) => setConfirmPassword(e.target.value)}
                required
              />
            </div>

            {error && (
              <div className="error"
                onClick={() => setError(null)}
              >{error}</div>
            )}

            <button
              className="primary-btn"
              type="submit"
              disabled={loading}
            >
              {loading ? "Регистрация..." : "Зарегистрироваться"}
            </button>
          </form>
        </div>
          <div className="flex-col card fade-in">
            <div className="justify-center">
              <h3>Есть аккаунт?</h3>
            </div>
            <button
              className="primary-btn flex-grow"
              onClick={() => navigate("/login")}
            >
              Войти
            </button>
          </div>
          <a onClick={() => navigate("/")}>... На главную</a>
      </div>
    </div>
  )
}
export default RegisterPage
