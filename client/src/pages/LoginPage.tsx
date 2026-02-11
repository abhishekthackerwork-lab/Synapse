// src/pages/LoginPage.tsx
import { useState } from 'react';
import {useNavigate} from "react-router-dom";
import { api } from '../api/client.ts';
import { useAuth } from "../context/AuthContext.tsx";
import { useError } from "../context/ErrorContext.tsx";

export default function LoginPage() {
    const [isRegistering, setIsRegistering] = useState(false);
    const [email, setEmail] = useState('');
    const [password, setPassword] = useState('');
    const [confirmPassword, setConfirmPassword] = useState('');
    const [isLoading, setIsLoading] = useState(false); // to prevent double clicks

    const { refreshUser } = useAuth();
    const { showError } = useError();
    const navigate = useNavigate();

const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();

        // --- PRE-FLIGHT CHECKS ---
        if (isRegistering && password !== confirmPassword) {
            showError("Passwords do not match!");
            return;
        }

        setIsLoading(true);

    try {
        if (isRegistering) {
            await api.post('/auth/register', { email, password });
        }

        // Backend handles the JWT/Session cookie here
        await api.post('/auth/login', { email, password });

        // Fetch user data and update global state
        await refreshUser();

        // Check if user was actually set
        console.log("Login sequence complete");
        navigate('/dashboard');
    } catch (err: any) {
        showError(err.message);
    } finally {
        setIsLoading(false);
    }
 };

return (
        <div className="flex min-h-screen items-center justify-center bg-slate-950 p-4">
            <form
                onSubmit={handleSubmit}
                className="flex w-full max-w-md flex-col gap-4 rounded-xl bg-slate-900 p-8 shadow-2xl border border-slate-800"
            >
                <h1 className="text-3xl font-bold text-white mb-2">
                    {isRegistering ? 'Join Synapse' : 'Welcome Back'}
                </h1>

                <input
                    type="email"
                    placeholder="Email"
                    className="rounded bg-slate-800 p-3 text-white outline-none focus:ring-2 focus:ring-blue-500"
                    value={email}
                    onChange={e => setEmail(e.target.value)}
                    required
                />

                <input
                    type="password"
                    placeholder="Password"
                    className="rounded bg-slate-800 p-3 text-white outline-none focus:ring-2 focus:ring-blue-500"
                    value={password}
                    onChange={e => setPassword(e.target.value)}
                    required
                />

                {/* --- CONDITIONAL FIELD --- */}
                {isRegistering && (
                    <input
                        type="password"
                        placeholder="Confirm Password"
                        className="rounded bg-slate-800 p-3 text-white outline-none focus:ring-2 focus:ring-blue-500 animate-in fade-in slide-in-from-top-2"
                        value={confirmPassword}
                        onChange={e => setConfirmPassword(e.target.value)}
                        required
                    />
                )}

                <button
                    type="submit"
                    disabled={isLoading}
                    className="mt-2 rounded bg-blue-600 p-3 font-bold text-white transition hover:bg-blue-500 disabled:opacity-50"
                >
                    {isLoading ? 'Processing...' : (isRegistering ? 'Create Account' : 'Sign In')}
                </button>

                <button
                    type="button" // CRITICAL: This ensures clicking the link doesn't submit the form!
                    onClick={() => {
                        setIsRegistering(!isRegistering);
                        setConfirmPassword(''); // Clear sensitive fields on toggle
                    }}
                    className="text-sm text-slate-400 hover:text-blue-400 transition"
                >
                    {isRegistering ? 'Already have an account? Sign In' : "New to Synapse? Register here"}
                </button>
            </form>
        </div>
    );
}