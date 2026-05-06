'use client';
import { useEffect, useState, useCallback } from 'react';
import { useRouter, usePathname } from 'next/navigation';
import Link from 'next/link';
import { 
  LayoutDashboard, Users, Briefcase, Shield, FileText, 
  Activity, LogOut, Bell, Wifi, WifiOff, Menu, X
} from 'lucide-react';
import { useWebSocket } from '@/hooks/useWebSocket';
import { useAuthStore } from '@/lib/store';

const NAV = [
  { href: '/dashboard',       label: 'Overview',  icon: LayoutDashboard },
  { href: '/dashboard/users', label: 'Usuarios',  icon: Users },
  { href: '/dashboard/jobs',  label: 'Jobs',      icon: Briefcase },
  { href: '/dashboard/otp',   label: 'OTP Panel', icon: Shield },
  { href: '/dashboard/logs',  label: 'Logs',      icon: FileText },
];

export default function DashboardLayout({ children }: { children: React.ReactNode }) {
  const router = useRouter();
  const pathname = usePathname();
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [otpCount, setOtpCount] = useState(0);
  const { connected, lastMessage } = useWebSocket();
  const { token, logout } = useAuthStore();

  useEffect(() => {
    if (!token) router.push('/');
  }, [token, router]);

  // Fetch pending OTP count
  useEffect(() => {
    const fetchOtp = async () => {
      try {
        const res = await fetch('/api/otp/pending/count', {
          headers: { Authorization: `Bearer ${token}` }
        });
        const data = await res.json();
        setOtpCount(data.count || 0);
      } catch {}
    };
    if (token) {
      fetchOtp();
      const interval = setInterval(fetchOtp, 10000);
      return () => clearInterval(interval);
    }
  }, [token]);

  // Handle OTP WebSocket updates
  useEffect(() => {
    if (lastMessage?.type === 'otp_required') {
      setOtpCount(c => c + 1);
    }
  }, [lastMessage]);

  const handleLogout = () => {
    logout();
    router.push('/');
  };

  if (!token) return null;

  return (
    <div className="min-h-screen bg-surface-950 flex">
      {/* Mobile overlay */}
      {sidebarOpen && (
        <div className="fixed inset-0 bg-black/60 z-20 lg:hidden" onClick={() => setSidebarOpen(false)} />
      )}

      {/* Sidebar */}
      <aside className={`
        fixed inset-y-0 left-0 z-30 w-60 bg-surface-900 border-r border-surface-800 flex flex-col
        transform transition-transform duration-200 lg:translate-x-0 lg:static lg:flex
        ${sidebarOpen ? 'translate-x-0' : '-translate-x-full'}
      `}>
        {/* Brand */}
        <div className="h-16 flex items-center gap-3 px-5 border-b border-surface-800">
          <div className="w-8 h-8 rounded-lg bg-brand-600/20 border border-brand-600/30 flex items-center justify-center flex-shrink-0">
            <Activity className="w-4 h-4 text-brand-400" />
          </div>
          <div>
            <span className="text-sm font-bold text-slate-100">CitaMonitor</span>
            <div className="flex items-center gap-1.5 mt-0.5">
              {connected
                ? <><Wifi className="w-2.5 h-2.5 text-emerald-400" /><span className="text-[10px] text-emerald-400">Live</span></>
                : <><WifiOff className="w-2.5 h-2.5 text-slate-500" /><span className="text-[10px] text-slate-500">Offline</span></>
              }
            </div>
          </div>
          <button className="ml-auto lg:hidden" onClick={() => setSidebarOpen(false)}>
            <X className="w-4 h-4 text-slate-400" />
          </button>
        </div>

        {/* Nav */}
        <nav className="flex-1 p-3 space-y-1 overflow-y-auto">
          {NAV.map(({ href, label, icon: Icon }) => {
            const active = pathname === href || (href !== '/dashboard' && pathname.startsWith(href));
            return (
              <Link key={href} href={href} onClick={() => setSidebarOpen(false)}
                className={active ? 'nav-item-active' : 'nav-item-inactive'}>
                <Icon className="w-4 h-4 flex-shrink-0" />
                <span>{label}</span>
                {href === '/dashboard/otp' && otpCount > 0 && (
                  <span className="ml-auto bg-red-500 text-white text-[10px] font-bold px-1.5 py-0.5 rounded-full min-w-[18px] text-center animate-pulse">
                    {otpCount}
                  </span>
                )}
              </Link>
            );
          })}
        </nav>

        {/* Footer */}
        <div className="p-3 border-t border-surface-800">
          <button onClick={handleLogout} className="nav-item-inactive w-full">
            <LogOut className="w-4 h-4" />
            <span>Cerrar sesión</span>
          </button>
        </div>
      </aside>

      {/* Main */}
      <div className="flex-1 flex flex-col min-w-0">
        {/* Top bar */}
        <header className="h-16 bg-surface-900/80 backdrop-blur border-b border-surface-800 flex items-center px-4 gap-3 sticky top-0 z-10">
          <button className="lg:hidden btn-ghost p-2" onClick={() => setSidebarOpen(true)}>
            <Menu className="w-5 h-5" />
          </button>
          <div className="flex-1" />
          {otpCount > 0 && (
            <Link href="/dashboard/otp"
              className="flex items-center gap-2 bg-red-500/10 border border-red-500/20 text-red-400 text-xs font-medium px-3 py-1.5 rounded-lg hover:bg-red-500/20 transition-colors animate-pulse-slow">
              <Shield className="w-3.5 h-3.5" />
              {otpCount} OTP pendiente{otpCount > 1 ? 's' : ''}
            </Link>
          )}
          <div className="text-xs text-slate-500 hidden sm:block">
            {new Date().toLocaleDateString('es-ES', { weekday: 'long', day: 'numeric', month: 'long' })}
          </div>
        </header>

        <main className="flex-1 p-6 overflow-auto animate-fade-in">
          {children}
        </main>
      </div>
    </div>
  );
}
