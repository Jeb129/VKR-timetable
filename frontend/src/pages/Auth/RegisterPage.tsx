import { useEffect, useState } from "react"
import { useLocation, useNavigate } from "react-router-dom"
import type { RegisterRequest } from "../../types/user"
import { useAuth } from "@/context/AuthContext"
import "@/styles/Auth.css";

const RegisterPage = () => {

  const { isAuthenticated, isLoading, register } = useAuth()
  const location = useLocation()
  const navigate = useNavigate()

  const [form, setForm] = useState<RegisterRequest>({
    username: "",
    email: "",
    password: "",
  })
  const [confirmPassword, setConfirmPassword] = useState("")

  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)


  const redirectedFrom = (location.state)?.from?.pathname
  const from = redirectedFrom || "/profile"
  useEffect(() => {
    if (!isLoading && isAuthenticated) {
      navigate(from, { replace: true });
    }
  }, [isAuthenticated, isLoading, navigate, from]);

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
      <div className="flex-col justify-center gap-2">
        <div className="flex-col card slide-up">
          <div className="justify-center">
            <h1 className="primary-text">Регистрация</h1>
          </div>
          <form className="flex-col gap-1" onSubmit={handleSubmit}>
            <div className="flex-col">
              <label>Имя</label>
              <input
                className="focus-glow border"
                name="username"
                value={form.username}
                onChange={handleChange}
                required
                autoComplete="username" 
              />
            </div>
            <div className="flex-col">
              <label>Email</label>
              <input
                className="focus-glow border"
                name="email"
                type="email"
                value={form.email}
                onChange={handleChange}
                required
                autoComplete="email" 
              />
            </div>

            <div className="flex-col">
              <label>Пароль</label>
              <input
                className="focus-glow border"
                name="password"
                type="password"
                value={form.password}
                onChange={handleChange}
                required
                autoComplete="new-password" 
              />
            </div>

            <div className="flex-col">
              <label>Повтор пароля</label>
              <input
                className="focus-glow border"
                name="password_confirmation"
                type="password"
                value={confirmPassword}
                onChange={(e) => setConfirmPassword(e.target.value)}
                required
                autoComplete="new-password" 
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
              className="secondary-btn flex-grow hover-lift"
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
