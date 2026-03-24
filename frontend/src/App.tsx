import { Route, Routes } from "react-router-dom"
import LoginPage from "./pages/Auth/LoginPage"
import RegisterPage from "./pages/Auth/RegisterPage"
import UserProfilePage from "./pages/UserProfilePage"

import './App.css'

// Основной контейнер приложения
const App = () =>
  <>
    <Routes>
      <Route path="/login" element={<LoginPage />} />
      <Route path="/register" element={<RegisterPage />} />
      <Route path="/profile" element={<UserProfilePage />} />
    </Routes>
  </>
export default App
