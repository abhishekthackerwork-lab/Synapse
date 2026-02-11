import React, { createContext,useContext,useState, useEffect } from 'react';
import { api } from "../api/client";

interface User {
    id: number;
    email: string;
    is_active: boolean;
}

interface AuthContextType {
    user: User | null;
    loading: boolean;
    login: (userData: User) => void;
    logout: () => void;
    refreshUser: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
    const [user, setUser] = useState<User | null>(null);
    const [loading, setLoading] = useState(true);

    const refreshUser = async () => {
        try {
            setLoading(true);
            // 'res' IS the user object because your wrapper returns 'data'
            const userData = await api.get<User>('/auth/me');
            setUser(userData);
        } catch (err) {
            setUser(null);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        refreshUser();
    }, []);

    const login = (userData: User) => setUser(userData);

    const logout = async () => {
    try {
        await api.post('/auth/logout', {}); // Tell backend to clear the cookie
    } finally {
        setUser(null);
        window.location.href = '/'; // Hard redirect to clean state
        }
    };

    return (
        <AuthContext.Provider value={{ user, loading, login, logout,refreshUser }}>
            {children}
        </AuthContext.Provider>
    );
};

// Custom hook for easy access
export const useAuth = () => {
    const context = useContext(AuthContext);
    if (!context) throw new Error("useAuth must be used within AuthProvider");
    return context;
};