import { ReactNode } from "react";
import Navbar from "./Navbar";

// Define the type for the props this component accepts
interface LayoutProps {
  children: ReactNode; // 'children' is the content we pass into the Layout
}

// Layout component wraps content with a Navbar and consistent styling
export default function Layout({ children }: LayoutProps) {
  return (
    // Sets dark mode background and minimum screen height
    <div className="min-h-screen bg-slate-950 text-slate-200">
      <Navbar />

      {/* The main content area, centered and padded */}
      <main className="max-w-7xl mx-auto px-6 py-8">
        {children}
      </main>
    </div>
  )
}