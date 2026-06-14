import { Navigate, useLocation } from "react-router-dom"
import { useAuth } from "@/context/AuthContext"
import type { ReactNode } from "react"

interface ProtectedRouteProps {
  children: ReactNode;
  adminOnly?: boolean;
  scheduleModOnly?: boolean;
  bookingModOnly?: boolean;
  anyModerator?: boolean;
}

export const ProtectedRoute = ({ 
  children, 
  adminOnly, 
  scheduleModOnly, 
  bookingModOnly,
  anyModerator 
}: ProtectedRouteProps) => {
  const { user, isAuthenticated, isLoading } = useAuth();
  const location = useLocation();
   
  if (isLoading) {
    return <div className="flex-row justify-center p-4">Загрузка...</div>;
  }

  // 1. Проверка авторизации
  if (!isAuthenticated) {
    return <Navigate to="/login" state={{ from: location }} replace />;
  }

  // 2. Логика проверки ролей 
  if (user?.is_staff) return <>{children}</>;

  if (adminOnly && !user?.is_staff) {
    return <Navigate to="/" replace />;
  }

  if (scheduleModOnly && !user?.is_schedule_moderator) {
    return <Navigate to="/" replace />;
  }

  if (bookingModOnly && !user?.is_booking_moderator) {
    return <Navigate to="/" replace />;
  }

  if (anyModerator && !(user?.is_booking_moderator || user?.is_schedule_moderator)) {
    return <Navigate to="/" replace />;
  }

  return <>{children}</>;
};
export default ProtectedRoute;
