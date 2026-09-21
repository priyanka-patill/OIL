import React from 'react';
import { useLocation } from 'react-router-dom';
import { Menu, Shield, Building2 } from 'lucide-react';
import { useAuth } from '../../context/AuthContext';

export const Header = ({ setMobileOpen }) => {
  const { user } = useAuth();
  const location = useLocation();

  const getPageTitle = (path) => {
    if (path === '/dashboard' || path === '/') return 'HSE Safety Analytics Dashboard';
    if (path === '/analytics') return 'Safety Intelligence';
    if (path === '/action-center') return 'HSE Action Center';
    if (path === '/actions/my') return 'My Actions';
    if (path === '/actions/assigned') return 'Assigned Actions';
    if (path.startsWith('/actions/')) return 'Action Details';
    if (path === '/reports') return 'Safety Reports';
    if (path === '/reports/new') return 'Submit Report';
    if (path.startsWith('/reports/')) return 'Report Details';
    if (path === '/admin/users') return 'User Management';
    if (path === '/admin/audit-logs') return 'Audit Trail';
    return 'HSE Safety Intelligence';
  };

  const pageTitle = getPageTitle(location.pathname);

  return (
    <header className="h-16 bg-slate-900/80 backdrop-blur-md border-b border-slate-800 sticky top-0 z-30 px-4 sm:px-6 flex items-center justify-between">
      <div className="flex items-center gap-3">
        <button
          onClick={() => setMobileOpen(true)}
          className="p-2 rounded-lg bg-slate-800 text-slate-300 hover:text-slate-100 lg:hidden"
        >
          <Menu className="w-5 h-5" />
        </button>

        <div className="hidden sm:flex items-center gap-2 text-xs text-slate-400">
          <Building2 className="w-4 h-4 text-amber-500" />
          <span className="font-semibold text-slate-200">{user?.site || 'Digboi Refinery'}</span>
          <span className="text-slate-600">•</span>
          <span>{user?.department || 'HSE Operations'}</span>
          <span className="text-slate-600">|</span>
          <span className="font-bold text-amber-400">{pageTitle}</span>
        </div>

        {/* Mobile Page Title Indicator */}
        <div className="sm:hidden text-xs font-bold text-amber-400 truncate max-w-[180px]">
          {pageTitle}
        </div>
      </div>

      <div className="flex items-center gap-4">
        <div className="flex items-center gap-2 px-3 py-1.5 rounded-full bg-slate-950/60 border border-slate-800 text-xs text-slate-300">
          <Shield className="w-3.5 h-3.5 text-emerald-400" />
          <span className="hidden md:inline">Platform Status:</span>
          <span className="text-emerald-400 font-semibold">Active & Live</span>
        </div>
      </div>
    </header>
  );
};
