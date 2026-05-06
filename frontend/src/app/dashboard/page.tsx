'use client';
import { useEffect, useState } from 'react';
import { Activity, Users, Briefcase, Shield, TrendingUp, CheckCircle, Clock, AlertCircle } from 'lucide-react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, AreaChart, Area } from 'recharts';
import { useAuthStore } from '@/lib/store';
import { useWebSocket } from '@/hooks/useWebSocket';

interface Stats {
  active_jobs: number;
  found_jobs: number;
  total_jobs: number;
  pending_otp: number;
  total_users: number;
  success_rate: number;
}

interface StatCardProps {
  label: string;
  value: string | number;
  icon: React.ElementType;
  color: string;
  sub?: string;
  pulse?: boolean;
}

function StatCard({ label, value, icon: Icon, color, sub, pulse }: StatCardProps) {
  return (
    <div className="stat-card">
      <div className="flex items-start justify-between">
        <div className={`w-10 h-10 rounded-xl flex items-center justify-center ${color}`}>
          <Icon className="w-5 h-5" />
        </div>
        {pulse && <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse mt-1" />}
      </div>
      <div>
        <p className="text-2xl font-bold text-slate-100">{value}</p>
        <p className="text-sm text-slate-500">{label}</p>
        {sub && <p className="text-xs text-slate-600 mt-0.5">{sub}</p>}
      </div>
    </div>
  );
}

const MOCK_CHART_DATA = Array.from({ length: 24 }, (_, i) => ({
  hour: `${i}:00`,
  checks: Math.floor(Math.random() * 200 + 50),
  found: Math.floor(Math.random() * 5),
}));

const JOB_STATUS_COLORS: Record<string, string> = {
  searching: 'badge-blue',
  found:     'badge-green',
  stopped:   'badge-gray',
  error:     'badge-red',
  queued:    'badge-yellow',
  paused:    'badge-yellow',
};

export default function DashboardPage() {
  const { token } = useAuthStore();
  const { lastMessage } = useWebSocket();
  const [stats, setStats] = useState<Stats | null>(null);
  const [recentJobs, setRecentJobs] = useState<any[]>([]);
  const [health, setHealth] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  const fetchData = async () => {
    if (!token) return;
    try {
      const headers = { Authorization: `Bearer ${token}` };
      const [statsRes, jobsRes, healthRes] = await Promise.all([
        fetch('/api/system/stats', { headers }),
        fetch('/api/jobs/?limit=5', { headers }),
        fetch('/api/system/health', { headers }),
      ]);
      setStats(await statsRes.json());
      setRecentJobs(await jobsRes.json());
      setHealth(await healthRes.json());
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { fetchData(); }, [token]);

  // Refresh on WS events
  useEffect(() => {
    if (lastMessage?.type && ['job_update', 'otp_required', 'appointment_found'].includes(lastMessage.type)) {
      fetchData();
    }
  }, [lastMessage]);

  // Auto-refresh every 30s
  useEffect(() => {
    const t = setInterval(fetchData, 30000);
    return () => clearInterval(t);
  }, [token]);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="w-8 h-8 border-2 border-brand-500 border-t-transparent rounded-full animate-spin" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-bold text-slate-100">Overview</h1>
          <p className="text-sm text-slate-500 mt-0.5">Monitoreo en tiempo real del sistema</p>
        </div>
        <div className="flex items-center gap-2">
          {health && (
            <div className={`badge ${health.status === 'healthy' ? 'badge-green' : 'badge-red'}`}>
              <span className={`w-1.5 h-1.5 rounded-full ${health.status === 'healthy' ? 'bg-emerald-400' : 'bg-red-400'} animate-pulse`} />
              {health.status === 'healthy' ? 'Sistema OK' : 'Degradado'}
            </div>
          )}
        </div>
      </div>

      {/* Stat cards */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard
          label="Jobs Activos"
          value={stats?.active_jobs ?? 0}
          icon={Activity}
          color="bg-brand-600/20 text-brand-400"
          sub="buscando ahora"
          pulse={!!stats?.active_jobs}
        />
        <StatCard
          label="Citas Encontradas"
          value={stats?.found_jobs ?? 0}
          icon={CheckCircle}
          color="bg-emerald-500/20 text-emerald-400"
          sub="total histórico"
        />
        <StatCard
          label="OTP Pendientes"
          value={stats?.pending_otp ?? 0}
          icon={Shield}
          color={stats?.pending_otp ? 'bg-red-500/20 text-red-400' : 'bg-slate-700/50 text-slate-400'}
          pulse={!!stats?.pending_otp}
        />
        <StatCard
          label="Usuarios"
          value={stats?.total_users ?? 0}
          icon={Users}
          color="bg-violet-500/20 text-violet-400"
        />
      </div>

      {/* Success rate + chart */}
      <div className="grid lg:grid-cols-3 gap-4">
        {/* Chart */}
        <div className="card lg:col-span-2">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-sm font-semibold text-slate-300">Actividad (24h)</h2>
            <span className="text-xs text-slate-600">Checks por hora</span>
          </div>
          <ResponsiveContainer width="100%" height={200}>
            <AreaChart data={MOCK_CHART_DATA}>
              <defs>
                <linearGradient id="grad" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#6366f1" stopOpacity={0.3} />
                  <stop offset="95%" stopColor="#6366f1" stopOpacity={0} />
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
              <XAxis dataKey="hour" tick={{ fontSize: 10, fill: '#475569' }} tickLine={false} axisLine={false} interval={3} />
              <YAxis tick={{ fontSize: 10, fill: '#475569' }} tickLine={false} axisLine={false} />
              <Tooltip
                contentStyle={{ background: '#0f172a', border: '1px solid #1e293b', borderRadius: 8, fontSize: 12 }}
                labelStyle={{ color: '#94a3b8' }}
              />
              <Area type="monotone" dataKey="checks" stroke="#6366f1" strokeWidth={2} fill="url(#grad)" dot={false} />
              <Area type="monotone" dataKey="found" stroke="#10b981" strokeWidth={2} fill="none" dot={false} />
            </AreaChart>
          </ResponsiveContainer>
        </div>

        {/* Health panel */}
        <div className="card space-y-4">
          <h2 className="text-sm font-semibold text-slate-300">Estado del Sistema</h2>
          <div className="space-y-3">
            {[
              { label: 'Base de Datos', key: 'database' },
              { label: 'Redis / Cache', key: 'redis' },
            ].map(({ label, key }) => (
              <div key={key} className="flex items-center justify-between">
                <span className="text-sm text-slate-400">{label}</span>
                <span className={`badge ${health?.[key] === 'ok' ? 'badge-green' : 'badge-red'}`}>
                  {health?.[key] ?? '—'}
                </span>
              </div>
            ))}
            <div className="flex items-center justify-between">
              <span className="text-sm text-slate-400">Tasa de Éxito</span>
              <span className="text-sm font-semibold text-emerald-400">{stats?.success_rate ?? 0}%</span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-sm text-slate-400">Total Jobs</span>
              <span className="text-sm text-slate-300">{stats?.total_jobs ?? 0}</span>
            </div>
          </div>
          <div className="pt-2 border-t border-surface-800">
            <div className="text-xs text-slate-600">Actualizado automáticamente cada 30s</div>
          </div>
        </div>
      </div>

      {/* Recent jobs */}
      <div className="card">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-sm font-semibold text-slate-300">Jobs Recientes</h2>
          <a href="/dashboard/jobs" className="text-xs text-brand-400 hover:text-brand-300">Ver todos →</a>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead>
              <tr className="border-b border-surface-800">
                <th className="th">ID</th>
                <th className="th">Usuario</th>
                <th className="th">Provincia</th>
                <th className="th">Trámite</th>
                <th className="th">Estado</th>
                <th className="th">Checks</th>
              </tr>
            </thead>
            <tbody>
              {recentJobs.length === 0 ? (
                <tr><td colSpan={6} className="td text-center text-slate-600 py-8">No hay jobs</td></tr>
              ) : recentJobs.map((job: any) => (
                <tr key={job.id} className="table-row">
                  <td className="td font-mono text-slate-500">#{job.id}</td>
                  <td className="td">{job.user_name || '—'}</td>
                  <td className="td">{job.province_name || '—'}</td>
                  <td className="td max-w-[200px] truncate">{job.tramite_name || '—'}</td>
                  <td className="td">
                    <span className={JOB_STATUS_COLORS[job.status] || 'badge-gray'}>
                      {job.status}
                    </span>
                  </td>
                  <td className="td font-mono">{job.check_count}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
