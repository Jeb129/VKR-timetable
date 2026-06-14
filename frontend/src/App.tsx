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
      <Route path="/login" element={<LoginPage />} />
      <Route path="/register" element={<RegisterPage />} />

      <Route path="/" element={<ProtectedRoute><HomePage /></ProtectedRoute>} />
      <Route path="/profile" element={<ProtectedRoute><UserProfilePage /></ProtectedRoute>} />
      <Route path="/schedule" element={<ProtectedRoute><SchedulePage /></ProtectedRoute>} />
      <Route path="/Booking" element={<ProtectedRoute><BookingCreatePage/></ProtectedRoute>}/>

      <Route path="/Statistics/:buildingId" element={<ProtectedRoute anyModerator={true}><BuildingStatsPage /></ProtectedRoute>} /> 
      <Route path="/Statistics" element={<ProtectedRoute anyModerator={true}><StatsPage/></ProtectedRoute>} />
      <Route path="/request" element={<ProtectedRoute anyModerator={true}><RequestsPage /></ProtectedRoute>} />
           
      <Route path="/Moderation" element={<ProtectedRoute bookingModOnly={true}><ModerationPage/></ProtectedRoute>}/>
      
      <Route path="/AcademicLoad" element={<ProtectedRoute scheduleModOnly={true}><AcademicLoadImportPage/></ProtectedRoute>}/>
      <Route path="/scenarios" element={<ProtectedRoute scheduleModOnly={true}><ScenarioSelectionPage /></ProtectedRoute>} />
      <Route path="/scenarios/:scenarioId/edit" element={<ProtectedRoute scheduleModOnly={true}><ScheduleEditorPage/></ProtectedRoute>}/>
      <Route path="/scenarios/:id" element={<ProtectedRoute scheduleModOnly={true}><ScenarioPage/></ProtectedRoute>}/>
      <Route path="/ScheduleEditor/:scenarioId/review" element={<ProtectedRoute scheduleModOnly={true}><ScenarioReviewPage /></ProtectedRoute>} />
      <Route path="/ScheduleEditor/:scenarioId/generate" element={<ProtectedRoute scheduleModOnly={true}><ScheduleGeneratorPage /></ProtectedRoute>} />
    </Routes>
  </>
export default App
