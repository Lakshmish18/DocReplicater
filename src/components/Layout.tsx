import { Link, useLocation } from 'react-router-dom';
import { FileText, Menu, X } from 'lucide-react';
import { useState } from 'react';

export default function Layout({ children }: { children: React.ReactNode }) {
  const location = useLocation();
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  const isActive = (path: string) => location.pathname === path;

  return (
    <div className="min-h-screen bg-white">
      {/* Navigation */}
      <nav className="fixed top-0 left-0 right-0 z-50 bg-white border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            {/* Logo */}
            <Link to="/" className="flex items-center space-x-2">
              <FileText className="h-8 w-8 text-blue-600" />
              <span className="text-xl font-semibold text-gray-900">Document Replicator</span>
            </Link>

            {/* Desktop Navigation */}
            <div className="hidden md:flex items-center space-x-8">
              <Link
                to="/"
                className={`text-sm font-medium transition-colors ${
                  isActive('/') ? 'text-blue-600' : 'text-gray-600 hover:text-gray-900'
                }`}
              >
                Home
              </Link>
              <a
                href="#how-it-works"
                className="text-sm font-medium text-gray-600 hover:text-gray-900 transition-colors"
              >
                How it Works
              </a>
              <Link
                to="/upload"
                className={`text-sm font-medium transition-colors ${
                  isActive('/upload') ? 'text-blue-600' : 'text-gray-600 hover:text-gray-900'
                }`}
              >
                Upload
              </Link>
            </div>

            {/* Auth Buttons */}
            <div className="hidden md:flex items-center space-x-4">
              <button className="text-sm font-medium text-gray-600 hover:text-gray-900 transition-colors">
                Login
              </button>
              <button className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg text-sm font-medium transition-colors">
                Sign Up
              </button>
            </div>

            {/* Mobile menu button */}
            <button
              onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
              className="md:hidden p-2"
            >
              {mobileMenuOpen ? <X className="h-6 w-6" /> : <Menu className="h-6 w-6" />}
            </button>
          </div>
        </div>

        {/* Mobile menu */}
        {mobileMenuOpen && (
          <div className="md:hidden bg-white border-t border-gray-200">
            <div className="px-4 py-4 space-y-4">
              <Link
                to="/"
                className="block text-sm font-medium text-gray-600 hover:text-gray-900"
                onClick={() => setMobileMenuOpen(false)}
              >
                Home
              </Link>
              <a
                href="#how-it-works"
                className="block text-sm font-medium text-gray-600 hover:text-gray-900"
                onClick={() => setMobileMenuOpen(false)}
              >
                How it Works
              </a>
              <Link
                to="/upload"
                className="block text-sm font-medium text-gray-600 hover:text-gray-900"
                onClick={() => setMobileMenuOpen(false)}
              >
                Upload
              </Link>
              <div className="pt-4 border-t border-gray-200 flex flex-col space-y-2">
                <button className="text-sm font-medium text-gray-600 text-left">Login</button>
                <button className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg text-sm font-medium">
                  Sign Up
                </button>
              </div>
            </div>
          </div>
        )}
      </nav>

      {/* Main content */}
      <main className="pt-16">
        {children}
      </main>
    </div>
  );
}