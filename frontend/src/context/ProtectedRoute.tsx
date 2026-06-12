import { Navigate, useLocation } from "react-router-dom"
import { useAuth } from "@/context/AuthContext"
import type { ReactNode } from "react"

interface ProtectedRouteProps {
  children: ReactNode
}

export const ProtectedRoute = ({ children }: ProtectedRouteProps) => {
  const { isAuthenticated, isLoading } = useAuth()
  const location = useLocation();
   
  if (isLoading) {
    return <div>Loading...</div>
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" state={{ from: location }} replace />;
  }

  return <>{children}</>
}
export default ProtectedRoute;
