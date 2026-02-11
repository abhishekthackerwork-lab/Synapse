// client/src/main.tsx
import React from 'react'
import ReactDOM from 'react-dom/client'
import App from './App.tsx'
import './index.css'
import { BrowserRouter } from 'react-router-dom'
import { AuthProvider } from './context/AuthContext'
import { ErrorProvider } from './context/ErrorContext'

ReactDOM.createRoot(document.getElementById('root')!).render(
    <React.StrictMode>
    {/* 2. Wrap the entire application tree */}
        <ErrorProvider>
            <BrowserRouter>
                <AuthProvider>
                    <App />
                </AuthProvider>
            </BrowserRouter>
        </ErrorProvider>
    </React.StrictMode>
)