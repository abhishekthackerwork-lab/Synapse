// client/src/context/ErrorContext.tsx
import React, { createContext, useContext, useState, ReactNode } from 'react';
import { createPortal } from 'react-dom'; // 1. Import createPortal

interface ErrorContextType {
    error: string | null;
    showError: (message: string) => void;
    clearError: () => void;
}

const ErrorContext = createContext<ErrorContextType | undefined>(undefined);

export const ErrorProvider = ({ children }: { children: ReactNode }) => {
    const [error, setError] = useState<string | null>(null);

    const showError = (message: string) => {
        setError(message);
        setTimeout(() => setError(null), 5000);
    };

    const clearError = () => setError(null);

    return (
        <ErrorContext.Provider value={{ error, showError, clearError }}>
            {children}

            {/* 2. Wrap the error UI in createPortal */}
            {error && createPortal(
                <div
                    style={{
                        position: 'fixed',
                        bottom: '20px',
                        right: '20px',
                        zIndex: 9999,
                        display: 'flex'
                    }}
                    className="animate-in fade-in slide-in-from-bottom-4"
                >
                    <div className="bg-red-600 border-2 border-red-400 text-white px-6 py-4 rounded-xl shadow-2xl flex items-center gap-3 min-w-[320px]">
                        <span className="text-2xl">⚠️</span>
                        <div className="flex flex-col">
                            <strong className="text-sm uppercase tracking-wide opacity-75">System Alert</strong>
                            <span className="font-medium text-lg">{error}</span>
                        </div>
                        <button
                            onClick={clearError}
                            className="ml-auto bg-white/20 hover:bg-white/40 p-2 rounded-lg transition-colors"
                        >
                            ✕
                        </button>
                    </div>
                </div>,
                document.body
            )}
        </ErrorContext.Provider>
    );
};

export const useError = () => {
    const context = useContext(ErrorContext);
    if (!context) throw new Error("useError must be used within ErrorProvider");
    return context;
};