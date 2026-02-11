import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider, useAuth } from './context/AuthContext';
import { ErrorProvider } from './context/ErrorContext';
import HomePage from './pages/HomePage';
import LoginPage from './pages/LoginPage';
import ChatPage from './pages/ChatPage';

function AppRoutes() {
    const { user, loading } = useAuth();

    if (loading) {
        return <div className="h-screen bg-slate-950 text-white p-10">System Booting...</div>;
    }

    return (
        <div className="min-h-screen bg-slate-950">
            <Routes>
                <Route path="/" element={<HomePage />} />
                <Route path="/login" element={!user ? <LoginPage /> : <Navigate to="/chat" />} />

                {/* CHANGE: Added :id? to make the ID optional but part of the path */}
                <Route
                    path="/chat/:id?"
                    element={user ? <ChatPage /> : <Navigate to="/login" />}
                />

                <Route path="*" element={<Navigate to="/" />} />
            </Routes>
        </div>
    );
}
export default function App() {
  return (
    <ErrorProvider>
      <AuthProvider>
        {/* Removed <BrowserRouter> from here because it's already in main.tsx */}
        <AppRoutes />
      </AuthProvider>
    </ErrorProvider>
  );
}