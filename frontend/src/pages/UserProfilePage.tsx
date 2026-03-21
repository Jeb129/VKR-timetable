import { useAuth } from "@/context/AuthContext"
import { Navigate } from "react-router-dom"

const UserProfilePage = () => {
    const {user, logout} = useAuth()
    if (!user) {
        return <Navigate to="/login" replace />
    }
    return (
        <div className="flex-col gap-20">
            <p>{user.username}</p>
            <p>{user.email}</p>
            <button onClick={logout}>Выйти</button>
        </div>
    )
}
export default UserProfilePage