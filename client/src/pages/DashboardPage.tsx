// client/src/pages/DashboardPage.tsx
import { useAuth } from '../context/AuthContext';
import { Navigate } from 'react-router-dom';

export default function DashboardPage() {
    const { user, loading } = useAuth();

    if (loading) return <div>Loading...</div>;

    // If no user, redirect to login (The "Guard")
    if (!user) return <Navigate to="/login" replace />;

    return (
        <div className="p-8 bg-slate-900 rounded-xl">
            <h1 className="text-3xl text-green-400">Welcome, {user.email}!</h1>
        </div>
    );
}