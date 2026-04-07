import { Route, Routes, Navigate  } from "react-router-dom"
import LoginPage from "./pages/Auth/LoginPage"
import RegisterPage from "./pages/Auth/RegisterPage"
import UserProfilePage from "./pages/UserProfilePage"
import SchedulePage from "./pages/Schedule/SchedulePage";
import BookingPage from "./pages/Booking/BookingPage";
import ModerationPage from "./pages/Booking/ModerationPage";
import ScheduleEditorPage from "./pages/Editor/ScheduleEditorPage";

import './App.css'

// Основной контейнер приложения
const App = () =>
  <>
    <Routes>
      <Route path="/" element={<Navigate to="/login" replace />} />
      <Route path="/login" element={<LoginPage />} />
      <Route path="/register" element={<RegisterPage />} />
      <Route path="/schedule" element={<SchedulePage />} />
      <Route path="/profile" element={<UserProfilePage />} />
      <Route path="/Booking" element={<BookingPage/>}/>
      <Route path="/Moderation" element={<ModerationPage/>}/>
      <Route path="/ScheduleEditor" element={<ScheduleEditorPage/>}/>
    </Routes>
  </>
export default App
