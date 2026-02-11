// client/src/components/Navbar.tsx (Only show changes)
import { Link } from 'react-router-dom';
import { useLogout } from '../hooks/useLogout'; // <-- NEW IMPORT

export default function Navbar() {
    const logout = useLogout(); // <-- NEW

    return (
        <nav className="bg-slate-900 border-b border-slate-800 text-white px-6 py-4">
          <div className="max-w-7xl mx-auto flex items-center justify-between">

            {/* Left Side: Logo / Link to Home */}
            <Link to="/" className="flex items-center gap-2"> {/* <-- Use Link here */}
              {/* ... Your Logo JSX ... */}
              <span className="text-xl font-semibold tracking-tight">Synapse</span>
            </Link>

            {/* Right Side: Navigation Links and Logout */}
            <div className="flex items-center gap-6 text-sm font-medium">
              <Link to="/" className="hover:text-white transition-colors text-slate-400">Home</Link>
              <Link to="/chat" className="hover:text-white transition-colors text-slate-400">Chat</Link>

              {/* LOGOUT BUTTON (NEW) */}
              <button
                onClick={logout} // <-- Call the hook function
                className="px-4 py-2 bg-red-600 hover:bg-red-700 rounded-md font-semibold text-white transition"
              >
                Logout
              </button>
            </div>

          </div>
        </nav>
    )
}