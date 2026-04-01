import { Route, Routes } from "react-router-dom"
import LoginPage from "./pages/Auth/LoginPage"
import RegisterPage from "./pages/Auth/RegisterPage"
import UserProfilePage from "./pages/UserProfilePage"
import SchedulePage from "./pages/Schedule/SchedulePage";
import BookingPage from "./pages/Booking/BookingPage";
import ModerationPage from "./pages/Booking/ModerationPage";
import './App.css'

// Основной контейнер приложения
const App = () =>
  <>
    <Routes>
      <Route path="/login" element={<LoginPage />} />
      <Route path="/register" element={<RegisterPage />} />
      <Route path="/schedule" element={<SchedulePage />} />
      <Route path="/profile" element={<UserProfilePage />} />
      <Route path="/Booking" element={<BookingPage/>}/>
      <Route path="/Moderation" element={<ModerationPage/>}/>
    </Routes>
  </>
export default App
