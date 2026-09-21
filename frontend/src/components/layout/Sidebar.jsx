import React from 'react';
import { NavLink } from 'react-router-dom';
import {
  LayoutDashboard,
  FileText,
  PlusCircle,
  Users,
  ShieldCheck,
  History,
  Cpu,
  LogOut,
  Flame,
  Sparkles,
  CheckSquare,
  Building2,
} from 'lucide-react';
import { useAuth } from '../../context/AuthContext';

export const Sidebar = ({ mobileOpen, setMobileOpen }) => {
  const { user, role, logout } = useAuth();

  const navItems = [
    {
      label: 'Dashboard',
      path: '/dashboard',
      icon: LayoutDashboard,
      roles: ['HSE_USER', 'HSE_MANAGER', 'ADMIN'],
    },
    {
      label: 'Safety Intelligence',
      path: '/analytics',
      icon: Sparkles,
      roles: ['HSE_USER', 'HSE_MANAGER', 'ADMIN'],
    },
    {
      label: 'HSE Action Center',
      path: '/action-center',
      icon: ShieldCheck,
      roles: ['HSE_USER', 'HSE_MANAGER', 'ADMIN'],
    },
    {
      label: 'My Actions',
      path: '/actions/my',
      icon: CheckSquare,
      roles: ['HSE_USER', 'HSE_MANAGER', 'ADMIN'],
    },
    {
      label: 'Assigned Actions',
      path: '/actions/assigned',
      icon: Building2,
      roles: ['HSE_MANAGER', 'ADMIN'],
    },
    {
      label: 'Safety Reports',
      path: '/reports',
      icon: FileText,
      roles: ['HSE_USER', 'HSE_MANAGER', 'ADMIN'],
    },
    {
      label: 'Submit Report',
      path: '/reports/new',
      icon: PlusCircle,
      roles: ['HSE_USER', 'HSE_MANAGER', 'ADMIN'],
    },
    {
      label: 'User Management',
      path: '/admin/users',
      icon: Users,
      roles: ['ADMIN'],
    },
    {
      label: 'Audit Trail',
      path: '/admin/audit-logs',
      icon: History,
      roles: ['ADMIN'],
    },
  ];

  const filteredNav = navItems.filter((item) => item.roles.includes(role));

  return (
    <>
      {/* Mobile Backdrop */}
      {mobileOpen && (
        <div
          className="fixed inset-0 bg-slate-950/80 backdrop-blur-sm z-40 lg:hidden"
          onClick={() => setMobileOpen(false)}
        />
      )}

      {/* Sidebar Container */}
      <aside
        className={`fixed top-0 bottom-0 left-0 z-50 w-64 bg-slate-900 border-r border-slate-800/80 flex flex-col transition-transform duration-300 ease-in-out lg:translate-x-0 ${
          mobileOpen ? 'translate-x-0' : '-translate-x-full'
        }`}
      >
        {/* Brand Header */}
        <div className="h-16 px-6 flex items-center gap-3 border-b border-slate-800 bg-slate-950/40">
          <div className="p-2 rounded-xl bg-amber-500/10 text-amber-500 border border-amber-500/20">
            <Flame className="w-6 h-6 fill-amber-500/20" />
          </div>
          <div>
            <h1 className="font-bold text-sm tracking-wide text-slate-100 uppercase">Oil India Limited</h1>
            <p className="text-[10px] text-amber-400 font-semibold uppercase tracking-wider">HSE SIF Analytics</p>
          </div>
        </div>

        {/* User Profile Card */}
        <div className="p-4 mx-3 my-4 rounded-xl bg-slate-950/50 border border-slate-800/80 flex items-center gap-3">
          <div className="w-9 h-9 rounded-full bg-gradient-to-tr from-amber-600 to-amber-400 flex items-center justify-center font-bold text-slate-950 text-sm shadow">
            {user?.name ? user.name.charAt(0).toUpperCase() : 'U'}
          </div>
          <div className="flex-1 min-w-0">
            <p className="text-xs font-semibold text-slate-200 truncate">{user?.name || 'Operator'}</p>
            <p className="text-[10px] text-slate-400 truncate">{user?.email}</p>
            <span className="inline-block mt-1 px-1.5 py-0.5 rounded text-[9px] font-extrabold uppercase bg-amber-500/10 text-amber-400 border border-amber-500/20">
              {role || 'HSE_USER'}
            </span>
          </div>
        </div>

        {/* Navigation Menu */}
        <nav className="flex-1 px-3 space-y-1 overflow-y-auto">
          <p className="px-3 text-[10px] font-bold text-slate-500 uppercase tracking-wider mb-2">Main Menu</p>
          {filteredNav.map((item) => {
            const Icon = item.icon;
            return (
              <NavLink
                key={item.path}
                to={item.path}
                end={item.path === '/reports'}
                onClick={() => setMobileOpen(false)}
                className={({ isActive }) =>
                  `flex items-center gap-3 px-3 py-2.5 rounded-xl text-xs font-medium transition-all ${
                    isActive
                      ? 'bg-amber-500/10 text-amber-400 border border-amber-500/20 font-semibold'
                      : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/60'
                  }`
                }
              >
                <Icon className="w-4 h-4 shrink-0" />
                <span>{item.label}</span>
              </NavLink>
            );
          })}
        </nav>

        {/* Footer Logout */}
        <div className="p-3 border-t border-slate-800">
          <button
            onClick={logout}
            className="w-full flex items-center justify-center gap-2 px-4 py-2 rounded-xl text-xs font-medium text-rose-400 hover:bg-rose-950/40 hover:border-rose-900/50 border border-transparent transition-all"
          >
            <LogOut className="w-4 h-4" />
            <span>Sign Out</span>
          </button>
        </div>
      </aside>
    </>
  );
};
