import { useAuth } from "../context/AuthContext";
import { Link } from "react-router-dom";

export default function HomePage() {
  const { user, logout } = useAuth(); // Added logout here

  return (
    <div className="relative min-h-screen w-full bg-slate-950 text-slate-200 selection:bg-blue-500/30 overflow-x-hidden">
      {/* 1. Navbar */}
      <nav className="flex justify-between items-center p-6 max-w-7xl mx-auto">
        <div className="text-2xl font-bold bg-gradient-to-r from-blue-400 to-indigo-500 bg-clip-text text-transparent">
          SYNAPSE
        </div>

        <div className="flex items-center gap-6">
          {user ? (
            <>
              <Link
                to="/chat"
                className="text-sm font-medium text-slate-400 hover:text-white transition-colors"
              >
                Dashboard
              </Link>
              <button
                onClick={logout}
                className="px-4 py-2 rounded-lg border border-red-500/30 text-red-500 hover:bg-red-500/10 transition-all text-xs font-bold uppercase tracking-wider"
              >
                Sign Out
              </button>
            </>
          ) : (
            <Link
              to="/login"
              className="text-sm font-medium text-slate-400 hover:text-white transition-colors"
            >
              Login
            </Link>
          )}
        </div>
      </nav>

      {/* 2. Hero Section */}
      <main className="w-full max-w-7xl mx-auto px-6 pt-20 pb-32 text-center">
        <h1 className="text-5xl md:text-7xl font-extrabold tracking-tight mb-6">
          Secure <span className="text-blue-500">Inference.</span>
        </h1>
        <p className="text-lg text-slate-400 max-w-2xl mx-auto mb-10">
          A high-performance RAG ecosystem utilizing Gemini 3.0, Vectorized storage, and
          enterprise-grade security via HashiCorp Vault.
        </p>

        <div className="flex justify-center gap-4">
          <Link
            to={user ? "/chat" : "/login"}
            className="px-8 py-4 bg-blue-600 hover:bg-blue-500 text-white rounded-xl font-bold text-lg shadow-lg shadow-blue-900/20 transition-all hover:-translate-y-1"
          >
            {user ? "Enter System" : "Get Started for Free"}
          </Link>
        </div>

        {/* 3. Feature Bento Grid */}
        <section className="grid md:grid-cols-3 gap-6 mt-32 text-left">
          <FeatureCard
            title="Advanced RAG"
            desc="Retrieval-Augmented Generation using Qdrant vector database for pinpoint accuracy."
            icon="🧠"
          />
          <FeatureCard
            title="Vault Security"
            desc="Dynamic database credentials and secrets managed by HashiCorp Vault."
            icon="🔒"
          />
          <FeatureCard
            title="FastAPI Engine"
            desc="Fully asynchronous Python backend ensuring sub-second latency."
            icon="⚡"
          />
        </section>
      </main>

      {/* 4. Tech Stack Footer */}
      <footer className="w-full border-t border-slate-900 bg-slate-950/50 py-12">
        <div className="max-w-7xl mx-auto px-6 flex flex-col md:flex-row justify-between items-center gap-6">
          <div className="text-slate-500 text-sm italic">Built for Portfolio.</div>
          <div className="flex gap-6 text-slate-400 grayscale opacity-50">
            <span>FastAPI</span>
            <span>React</span>
            <span>PostgreSQL</span>
            <span>Gemini</span>
          </div>
        </div>
      </footer>
    </div>
  );
}

function FeatureCard({ title, desc, icon }: { title: string; desc: string; icon: string }) {
  return (
    <div className="p-8 rounded-2xl bg-slate-900/50 border border-slate-800 hover:border-blue-500/50 transition-colors group">
      <div className="text-3xl mb-4 group-hover:scale-110 transition-transform">{icon}</div>
      <h3 className="text-xl font-bold mb-2">{title}</h3>
      <p className="text-slate-400 text-sm leading-relaxed">{desc}</p>
    </div>
  );
}