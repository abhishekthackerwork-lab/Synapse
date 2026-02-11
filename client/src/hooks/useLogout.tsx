// client/src/hooks/useLogout.ts
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';

export const useLogout = () => {
    const navigate = useNavigate();

    const logout = async () => {
        try {
            // Call the FastAPI logout endpoint
            const response = await fetch('http://localhost:8000/api/v1/auth/logout', {
                method: 'POST',
                credentials: 'include', // Needed to ensure the cookie is sent for deletion
            });

            if (response.ok) {
                // If the backend successfully deleted the cookie
                console.log("Logged out successfully. Redirecting.");
                navigate('/login');
            } else {
                console.error("Logout failed on server.");
                // Even if the server fails, redirect the user to clear the UI
                navigate('/login');
            }
        }
        catch (error) {
            console.error("Network error during logout:", error);
            // On any network error, redirect the user immediately
            navigate('/login');
        }
        finally {
            // 2. Unify State: clear the react "user" regardless of API success
            clearAuthState();

            // 3. Redirect the user to the login screen
            navigate('/login')
        }
    };

    return logout;
};