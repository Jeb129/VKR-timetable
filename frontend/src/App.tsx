import { Route, Routes, Navigate  } from "react-router-dom"
import LoginPage from "./pages/Auth/LoginPage"
import ProtectedRoute from "./context/ProtectedRoute"
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
      <Route path="/schedule" element={<ProtectedRoute><SchedulePage /></ProtectedRoute>} />
      <Route path="/profile" element={<ProtectedRoute><UserProfilePage /></ProtectedRoute>} />
      <Route path="/Booking" element={<ProtectedRoute><BookingPage/></ProtectedRoute>}/>
      <Route path="/Moderation" element={<ProtectedRoute><ModerationPage/></ProtectedRoute>}/>
      <Route path="/ScheduleEditor" element={<ProtectedRoute><ScheduleEditorPage/></ProtectedRoute>}/>
    </Routes>
  </>
export default App
