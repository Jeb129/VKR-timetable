import { Route, Routes, Navigate  } from "react-router-dom"
import LoginPage from "./pages/Auth/LoginPage"
import ProtectedRoute from "./context/ProtectedRoute"
import RegisterPage from "./pages/Auth/RegisterPage"
import UserProfilePage from "./pages/UserProfilePage"
import SchedulePage from "./pages/Schedule/SchedulePage";
import BookingPage from "./pages/Booking/BookingPage";
import ModerationPage from "./pages/Booking/ModerationPage";
import ScheduleEditorPage from "./pages/Editor/ScheduleEditorPage";
import ScenarioSelectionPage from "./pages/Editor/ScenarioSelectionPage";
import TeacherAdjustmentPage from "./pages/TeacherAdjustment/TeacherAdjustmentPage"
import AcademicLoadImportPage from "./pages/AcademicLoad/AcademicLoadImportPage"
import HomePage from "./pages/HomePage";

import './App.css'

// Основной контейнер приложения
const App = () =>
  <>
    <Routes>
      <Route path="/" element={<ProtectedRoute><HomePage /></ProtectedRoute>} />
      <Route path="/login" element={<LoginPage />} />
      <Route path="/register" element={<RegisterPage />} />
      <Route path="/schedule" element={<ProtectedRoute><SchedulePage /></ProtectedRoute>} />
      <Route path="/profile" element={<ProtectedRoute><UserProfilePage /></ProtectedRoute>} />
      <Route path="/Booking" element={<ProtectedRoute><BookingPage/></ProtectedRoute>}/>
      <Route path="/Moderation" element={<ProtectedRoute><ModerationPage/></ProtectedRoute>}/>
      <Route path="/ScheduleEditor" element={<ProtectedRoute><ScenarioSelectionPage /></ProtectedRoute>} />
      <Route path="/ScheduleEditor/:scenarioId" element={<ProtectedRoute><ScheduleEditorPage/></ProtectedRoute>}/>
      <Route path="/TeacherAdjustment" element={<ProtectedRoute><TeacherAdjustmentPage/></ProtectedRoute>}/>
      <Route path="/AcademicLoad" element={<ProtectedRoute><AcademicLoadImportPage/></ProtectedRoute>}/>
    </Routes>
  </>
export default App
