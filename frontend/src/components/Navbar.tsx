'use client';

import React, { useState } from 'react';
import Link from 'next/link';
import { useAuth } from '@/src/lib/auth-context';
import { Menu, X, ChevronDown, User, LogOut, LayoutDashboard, FileText } from 'lucide-react';

export default function Navbar() {
  const { isAuthenticated, user, logout } = useAuth();
  const [mobileOpen, setMobileOpen] = useState(false);
  const [userMenuOpen, setUserMenuOpen] = useState(false);

  return (
    <nav className="sticky top-0 z-50 bg-white/95 backdrop-blur-sm border-b border-gray-200 shadow-sm">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          {/* Logo */}
          <Link href="/" className="flex items-center gap-2">
            <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-orange-500 to-orange-700 flex items-center justify-center">
              <span className="text-white font-bold text-sm">O</span>
            </div>
            <span className="text-xl font-bold text-gray-900">
              Orange<span className="text-orange-600">Fi</span>
            </span>
          </Link>

          {/* Desktop nav links */}
          <div className="hidden md:flex items-center gap-6">
            <Link href="/" className="text-gray-600 hover:text-orange-600 transition-colors text-sm font-medium">
              Home
            </Link>
            {isAuthenticated ? (
              <>
                <Link href="/dashboard" className="text-gray-600 hover:text-orange-600 transition-colors text-sm font-medium">
                  Dashboard
                </Link>
                <Link href="/applications" className="text-gray-600 hover:text-orange-600 transition-colors text-sm font-medium">
                  Applications
                </Link>
                <Link href="/loans" className="text-gray-600 hover:text-orange-600 transition-colors text-sm font-medium">
                  Loans
                </Link>
                <Link href="/pre-qualify" className="text-gray-600 hover:text-orange-600 transition-colors text-sm font-medium">
                  Apply
                </Link>
              </>
            ) : (
              <Link href="/pre-qualify" className="text-gray-600 hover:text-orange-600 transition-colors text-sm font-medium">
                Check Rate
              </Link>
            )}
          </div>

          {/* Auth buttons — Desktop */}
          <div className="hidden md:flex items-center gap-3">
            {isAuthenticated ? (
              <div className="relative">
                <button
                  onClick={() => setUserMenuOpen(!userMenuOpen)}
                  className="flex items-center gap-2 px-3 py-2 rounded-lg hover:bg-gray-100 transition-colors"
                >
                  <div className="w-8 h-8 rounded-full bg-orange-100 flex items-center justify-center">
                    <User className="w-4 h-4 text-orange-600" />
                  </div>
                  <span className="text-sm font-medium text-gray-700">
                    {user?.first_name || 'User'}
                  </span>
                  <ChevronDown className="w-4 h-4 text-gray-400" />
                </button>

                {userMenuOpen && (
                  <>
                    <div className="fixed inset-0 z-10" onClick={() => setUserMenuOpen(false)} />
                    <div className="absolute right-0 mt-2 w-56 bg-white rounded-xl shadow-lg border border-gray-200 py-2 z-20 slide-up">
                      <div className="px-4 py-2 border-b border-gray-100">
                        <p className="text-sm font-medium text-gray-900">{user?.first_name} {user?.last_name}</p>
                        <p className="text-xs text-gray-500">{user?.email}</p>
                      </div>
                      <Link
                        href="/dashboard"
                        className="flex items-center gap-2 px-4 py-2 text-sm text-gray-700 hover:bg-gray-50"
                        onClick={() => setUserMenuOpen(false)}
                      >
                        <LayoutDashboard className="w-4 h-4" />
                        Dashboard
                      </Link>
                      <button
                        onClick={() => {
                          setUserMenuOpen(false);
                          logout();
                        }}
                        className="flex items-center gap-2 px-4 py-2 text-sm text-red-600 hover:bg-red-50 w-full text-left"
                      >
                        <LogOut className="w-4 h-4" />
                        Sign Out
                      </button>
                    </div>
                  </>
                )}
              </div>
            ) : (
              <>
                <Link
                  href="/login"
                  className="px-4 py-2 text-sm font-medium text-gray-700 hover:text-orange-600 transition-colors"
                >
                  Sign In
                </Link>
                <Link
                  href="/register"
                  className="px-5 py-2.5 text-sm font-medium text-white bg-orange-600 rounded-lg hover:bg-orange-700 transition-colors shadow-sm"
                >
                  Get Started
                </Link>
              </>
            )}
          </div>

          {/* Mobile hamburger */}
          <button
            onClick={() => setMobileOpen(!mobileOpen)}
            className="md:hidden p-2 rounded-lg hover:bg-gray-100"
            aria-label="Toggle menu"
          >
            {mobileOpen ? <X className="w-6 h-6" /> : <Menu className="w-6 h-6" />}
          </button>
        </div>
      </div>

      {/* Mobile menu */}
      {mobileOpen && (
        <div className="md:hidden border-t border-gray-200 bg-white slide-down">
          <div className="px-4 py-3 space-y-1">
            <Link
              href="/"
              className="block px-3 py-2 rounded-lg text-gray-700 hover:bg-orange-50 hover:text-orange-600"
              onClick={() => setMobileOpen(false)}
            >
              Home
            </Link>
            {isAuthenticated ? (
              <>
                <Link
                  href="/dashboard"
                  className="block px-3 py-2 rounded-lg text-gray-700 hover:bg-orange-50 hover:text-orange-600"
                  onClick={() => setMobileOpen(false)}
                >
                  Dashboard
                </Link>
                <Link
                  href="/applications"
                  className="block px-3 py-2 rounded-lg text-gray-700 hover:bg-orange-50 hover:text-orange-600"
                  onClick={() => setMobileOpen(false)}
                >
                  Applications
                </Link>
                <Link
                  href="/loans"
                  className="block px-3 py-2 rounded-lg text-gray-700 hover:bg-orange-50 hover:text-orange-600"
                  onClick={() => setMobileOpen(false)}
                >
                  Loans
                </Link>
                <Link
                  href="/payments"
                  className="block px-3 py-2 rounded-lg text-gray-700 hover:bg-orange-50 hover:text-orange-600"
                  onClick={() => setMobileOpen(false)}
                >
                  Payments
                </Link>
                <Link
                  href="/pre-qualify"
                  className="block px-3 py-2 rounded-lg text-gray-700 hover:bg-orange-50 hover:text-orange-600"
                  onClick={() => setMobileOpen(false)}
                >
                  Apply for Loan
                </Link>
                <hr className="my-2" />
                {user && (
                  <div className="px-3 py-2 text-sm text-gray-500">
                    Signed in as <span className="font-medium text-gray-700">{user.first_name}</span>
                  </div>
                )}
                <button
                  onClick={() => {
                    setMobileOpen(false);
                    logout();
                  }}
                  className="block w-full text-left px-3 py-2 rounded-lg text-red-600 hover:bg-red-50"
                >
                  Sign Out
                </button>
              </>
            ) : (
              <>
                <Link
                  href="/login"
                  className="block px-3 py-2 rounded-lg text-gray-700 hover:bg-orange-50 hover:text-orange-600"
                  onClick={() => setMobileOpen(false)}
                >
                  Sign In
                </Link>
                <Link
                  href="/register"
                  className="block px-3 py-2 rounded-lg text-white bg-orange-600 hover:bg-orange-700 text-center"
                  onClick={() => setMobileOpen(false)}
                >
                  Get Started
                </Link>
              </>
            )}
          </div>
        </div>
      )}
    </nav>
  );
}
