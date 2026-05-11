'use client';

import React, { useState, useEffect } from 'react';
import Link from 'next/link';
import { usePathname, useRouter } from 'next/navigation';
import { AdminAuthProvider, useAdminAuth } from '@/src/lib/admin-auth-context';
import { getAdminAccessToken } from '@/src/lib/admin-api';
import {
  LayoutDashboard,
  FileText,
  CreditCard,
  Users,
  Shield,
  ScrollText,
  Briefcase,
  Settings,
  ChevronLeft,
  ChevronRight,
  Menu,
  X,
  LogOut,
  User,
  ChevronDown,
  Loader2,
} from 'lucide-react';

// ── Navigation items ─────────────────────────────────────────────────────────

const NAV_ITEMS = [
  { label: 'Dashboard', href: '/admin/dashboard', icon: LayoutDashboard },
  { label: 'Applications', href: '/admin/applications', icon: FileText, badge: true },
  { label: 'Loans', href: '/admin/loans', icon: CreditCard },
  { label: 'Borrowers', href: '/admin/borrowers', icon: Users },
  { label: 'Compliance', href: '/admin/compliance', icon: Shield },
  { label: 'Audit Log', href: '/admin/audit-log', icon: ScrollText },
  { label: 'Portfolio', href: '/admin/portfolio', icon: Briefcase },
  { label: 'Settings', href: '/admin/settings', icon: Settings },
];

// ── Auth Guard ───────────────────────────────────────────────────────────────

function AdminAuthGuard({ children }: { children: React.ReactNode }) {
  const { isAuthenticated, loading } = useAdminAuth();
  const router = useRouter();
  const pathname = usePathname();

  useEffect(() => {
    if (!loading && !isAuthenticated && !getAdminAccessToken()) {
      router.push('/admin/login');
    }
  }, [loading, isAuthenticated, router, pathname]);

  // Allow the login page to render even when not authenticated
  const isLoginPage = pathname === '/admin/login';

  if (loading && !isLoginPage) {
    return (
      <div className="min-h-screen bg-gray-950 flex items-center justify-center">
        <div className="flex flex-col items-center gap-3">
          <Loader2 className="w-8 h-8 text-orange-500 animate-spin" />
          <p className="text-sm text-gray-400">Verifying session...</p>
        </div>
      </div>
    );
  }

  if (!isAuthenticated && !isLoginPage) {
    return (
      <div className="min-h-screen bg-gray-950 flex items-center justify-center">
        <Loader2 className="w-8 h-8 text-orange-500 animate-spin" />
      </div>
    );
  }

  return <>{children}</>;
}

// ── Sidebar ──────────────────────────────────────────────────────────────────

function AdminSidebar({
  collapsed,
  onToggle,
  mobileOpen,
  onMobileClose,
}: {
  collapsed: boolean;
  onToggle: () => void;
  mobileOpen: boolean;
  onMobileClose: () => void;
}) {
  const pathname = usePathname();
  const { user, logout } = useAdminAuth();
  const [userMenuOpen, setUserMenuOpen] = useState(false);

  const isActive = (href: string) => {
    if (href === '/admin/dashboard') return pathname === href;
    return pathname.startsWith(href);
  };

  const sidebarContent = (
    <div className="flex flex-col h-full">
      {/* Logo */}
      <div className="flex items-center justify-between px-4 h-16 border-b border-white/5">
        <Link href="/admin/dashboard" className="flex items-center gap-2.5 min-w-0">
          <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-orange-500 to-orange-700 flex items-center justify-center flex-shrink-0">
            <span className="text-white font-bold text-sm">O</span>
          </div>
          {!collapsed && (
            <div className="truncate">
              <span className="text-white font-bold text-sm">OrangeFi</span>
              <span className="text-orange-400 font-bold text-sm"> Admin</span>
            </div>
          )}
        </Link>
        <button
          onClick={onMobileClose || onToggle}
          className="lg:hidden p-1 rounded-lg hover:bg-white/10 text-gray-400 hover:text-white"
        >
          <X className="w-5 h-5" />
        </button>
      </div>

      {/* Nav items */}
      <nav className="flex-1 py-4 px-3 space-y-1 overflow-y-auto">
        {NAV_ITEMS.map((item) => {
          const Icon = item.icon;
          const active = isActive(item.href);
          return (
            <Link
              key={item.href}
              href={item.href}
              onClick={onMobileClose}
              className={`flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm font-medium transition-all ${
                active
                  ? 'bg-orange-500/15 text-orange-400 border border-orange-500/20'
                  : 'text-gray-400 hover:text-white hover:bg-white/5 border border-transparent'
              }`}
              title={collapsed ? item.label : undefined}
            >
              <Icon className="w-5 h-5 flex-shrink-0" />
              {!collapsed && (
                <span className="truncate flex-1">{item.label}</span>
              )}
              {!collapsed && item.badge && (
                <span className="w-2 h-2 rounded-full bg-orange-500 animate-pulse" />
              )}
            </Link>
          );
        })}
      </nav>

      {/* User profile */}
      <div className="border-t border-white/5 p-3">
        <div className="relative">
          <button
            onClick={() => setUserMenuOpen(!userMenuOpen)}
            className={`flex items-center gap-3 w-full px-3 py-2.5 rounded-xl hover:bg-white/5 transition-all ${
              collapsed ? 'justify-center' : ''
            }`}
          >
            <div className="w-8 h-8 rounded-full bg-gradient-to-br from-orange-400 to-orange-600 flex items-center justify-center flex-shrink-0">
              <User className="w-4 h-4 text-white" />
            </div>
            {!collapsed && (
              <>
                <div className="flex-1 text-left min-w-0">
                  <p className="text-sm font-medium text-white truncate">
                    {user?.name || 'Admin'}
                  </p>
                  <p className="text-xs text-gray-500 truncate capitalize">
                    {user?.role || 'Administrator'}
                  </p>
                </div>
                <ChevronDown className="w-4 h-4 text-gray-500" />
              </>
            )}
          </button>

          {userMenuOpen && !collapsed && (
            <>
              <div className="fixed inset-0 z-10" onClick={() => setUserMenuOpen(false)} />
              <div className="absolute bottom-full left-3 right-3 mb-2 bg-gray-800 rounded-xl border border-white/10 shadow-xl py-2 z-20 slide-up">
                <div className="px-4 py-2 border-b border-white/5">
                  <p className="text-sm font-medium text-white">{user?.name || 'Admin'}</p>
                  <p className="text-xs text-gray-400">{user?.email || ''}</p>
                </div>
                <button
                  onClick={() => { setUserMenuOpen(false); logout(); }}
                  className="flex items-center gap-2 w-full px-4 py-2.5 text-sm text-red-400 hover:bg-white/5 transition-colors"
                >
                  <LogOut className="w-4 h-4" />
                  Sign Out
                </button>
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  );

  return (
    <>
      {/* Desktop sidebar */}
      <aside
        className={`hidden lg:flex flex-col bg-gray-900 border-r border-white/5 transition-all duration-300 ${
          collapsed ? 'w-[72px]' : 'w-64'
        }`}
      >
        {sidebarContent}

        {/* Collapse toggle */}
        <button
          onClick={onToggle}
          className="absolute -right-3 top-20 w-6 h-6 rounded-full bg-gray-800 border border-white/10 flex items-center justify-center text-gray-400 hover:text-white hover:bg-gray-700 transition-all shadow-lg"
        >
          {collapsed ? (
            <ChevronRight className="w-3.5 h-3.5" />
          ) : (
            <ChevronLeft className="w-3.5 h-3.5" />
          )}
        </button>
      </aside>

      {/* Mobile overlay */}
      {mobileOpen && (
        <div className="fixed inset-0 z-50 lg:hidden">
          <div className="absolute inset-0 bg-black/60 backdrop-blur-sm" onClick={onMobileClose} />
          <aside className="relative w-72 h-full bg-gray-900 border-r border-white/5 shadow-2xl animate-slideIn">
            {sidebarContent}
          </aside>
        </div>
      )}

      <style jsx>{`
        @keyframes slideIn {
          from { transform: translateX(-100%); }
          to { transform: translateX(0); }
        }
        .animate-slideIn {
          animation: slideIn 0.2s ease-out;
        }
        .slide-up {
          animation: slideUp 0.15s ease-out;
        }
        @keyframes slideUp {
          from { opacity: 0; transform: translateY(5px); }
          to { opacity: 1; transform: translateY(0); }
        }
      `}</style>
    </>
  );
}

// ── Main Layout ──────────────────────────────────────────────────────────────

function AdminLayoutContent({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const [collapsed, setCollapsed] = useState(true);
  const [mobileOpen, setMobileOpen] = useState(false);
  const { user, logout } = useAdminAuth();

  // Close mobile menu on route change
  useEffect(() => {
    setMobileOpen(false);
  }, [pathname]);

  // If on login page, render without sidebar
  if (pathname === '/admin/login') {
    return <>{children}</>;
  }

  const getPageTitle = () => {
    const item = NAV_ITEMS.find((i) =>
      i.href === '/admin/dashboard' ? pathname === i.href : pathname.startsWith(i.href)
    );
    return item?.label || 'Admin';
  };

  return (
    <div className="min-h-screen bg-gray-950 flex">
      <AdminSidebar
        collapsed={collapsed}
        onToggle={() => setCollapsed(!collapsed)}
        mobileOpen={mobileOpen}
        onMobileClose={() => setMobileOpen(false)}
      />

      {/* Main area */}
      <div className="flex-1 flex flex-col min-w-0">
        {/* Top bar (mobile) */}
        <header className="lg:hidden flex items-center justify-between px-4 h-14 bg-gray-900 border-b border-white/5">
          <button
            onClick={() => setMobileOpen(true)}
            className="p-2 rounded-lg hover:bg-white/5 text-gray-400"
          >
            <Menu className="w-5 h-5" />
          </button>
          <div className="flex items-center gap-2">
            <div className="w-6 h-6 rounded-md bg-gradient-to-br from-orange-500 to-orange-700 flex items-center justify-center">
              <span className="text-white font-bold text-xs">O</span>
            </div>
            <span className="text-sm font-semibold text-white">Admin</span>
          </div>
          <button
            onClick={logout}
            className="p-2 rounded-lg hover:bg-white/5 text-gray-400"
          >
            <LogOut className="w-5 h-5" />
          </button>
        </header>

        {/* Page content */}
        <main className="flex-1 overflow-y-auto">
          {children}
        </main>
      </div>
    </div>
  );
}

// ── Exported Layout ──────────────────────────────────────────────────────────

export default function AdminLayout({ children }: { children: React.ReactNode }) {
  return (
    <AdminAuthProvider>
      <AdminAuthGuard>
        <AdminLayoutContent>{children}</AdminLayoutContent>
      </AdminAuthGuard>
    </AdminAuthProvider>
  );
}
