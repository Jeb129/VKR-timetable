import { Route, Routes} from "react-router-dom"
import LoginPage from "./pages/Auth/LoginPage"
import ProtectedRoute from "./context/ProtectedRoute"
import RegisterPage from "./pages/Auth/RegisterPage"
import UserProfilePage from "./pages/UserProfilePage"
import SchedulePage from "./pages/Schedule/SchedulePage";
import ModerationPage from "./pages/Booking/ModerationPage";
import ScheduleEditorPage from "./pages/Editor/ScheduleEditorPage";
import ScenarioSelectionPage from "./pages/Editor/ScenarioSelectionPage";
import AcademicLoadImportPage from "./pages/AcademicLoad/AcademicLoadImportPage"
import HomePage from "./pages/HomePage";
import StatsPage from "./pages/Statistics/StatsPage"
import BuildingStatsPage from "./pages/Statistics/BuildingStatsPage"
import ScenarioReviewPage from "./pages/Editor/ScenarioReviewPage"
import ScheduleGeneratorPage from "./pages/Editor/ScheduleGeneratorPage"
import BookingCreatePage from "./pages/Booking/BookingCreatePage"

import './App.css'
import { RequestsPage } from "./pages/RequestsPage"
import ScenarioPage from "./pages/Schedule/ScenarioPage"

// Основной контейнер приложения
const App = () =>
  <>
    <Routes>
      <Route path="/" element={<ProtectedRoute><HomePage /></ProtectedRoute>} />
      <Route path="/login" element={<LoginPage />} />
      <Route path="/register" element={<RegisterPage />} />
      <Route path="/schedule" element={<ProtectedRoute><SchedulePage /></ProtectedRoute>} />
      <Route path="/request" element={<ProtectedRoute><RequestsPage /></ProtectedRoute>} />
      <Route path="/profile" element={<ProtectedRoute><UserProfilePage /></ProtectedRoute>} />
      <Route path="/Booking" element={<ProtectedRoute><BookingCreatePage/></ProtectedRoute>}/>
      <Route path="/Moderation" element={<ProtectedRoute><ModerationPage/></ProtectedRoute>}/>
      <Route path="/scenarios" element={<ProtectedRoute><ScenarioSelectionPage /></ProtectedRoute>} />
      <Route path="/ScheduleEditor/:scenarioId" element={<ProtectedRoute><ScheduleEditorPage/></ProtectedRoute>}/>
      <Route path="/scenarios/:id" element={<ProtectedRoute><ScenarioPage/></ProtectedRoute>}/>
      <Route path="/AcademicLoad" element={<ProtectedRoute><AcademicLoadImportPage/></ProtectedRoute>}/>
      <Route path="/Statistics" element={<ProtectedRoute><StatsPage/></ProtectedRoute>} />
      <Route path="/Statistics/:buildingId" element={<ProtectedRoute><BuildingStatsPage /></ProtectedRoute>} />
      <Route path="/ScheduleEditor/:scenarioId/review" element={<ProtectedRoute><ScenarioReviewPage /></ProtectedRoute>} />
      <Route path="/ScheduleEditor/:scenarioId/generate" element={<ProtectedRoute><ScheduleGeneratorPage /></ProtectedRoute>} />
    </Routes>
  </>
export default App
