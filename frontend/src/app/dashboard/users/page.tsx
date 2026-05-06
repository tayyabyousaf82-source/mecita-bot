'use client';
import { useEffect, useState, useCallback } from 'react';
import { Search, UserX, UserCheck, Calendar, Briefcase } from 'lucide-react';
import { useAuthStore } from '@/lib/store';
import { formatDistanceToNow } from 'date-fns';
import { es } from 'date-fns/locale';

export default function UsersPage() {
  const { token } = useAuthStore();
  const [users, setUsers] = useState<any[]>([]);
  const [stats, setStats] = useState<any>({});
  const [search, setSearch] = useState('');
  const [loading, setLoading] = useState(true);
  const [banLoading, setBanLoading] = useState<number | null>(null);

  const headers = { Authorization: `Bearer ${token}` };

  const fetchUsers = useCallback(async () => {
    try {
      const params = search ? `?search=${encodeURIComponent(search)}` : '';
      const [usersRes, statsRes] = await Promise.all([
        fetch(`/api/users/${params}`, { headers }),
        fetch('/api/users/stats', { headers }),
      ]);
      setUsers(await usersRes.json());
      setStats(await statsRes.json());
    } catch (e) { console.error(e); }
    finally { setLoading(false); }
  }, [token, search]);

  useEffect(() => {
    const t = setTimeout(fetchUsers, search ? 400 : 0);
    return () => clearTimeout(t);
  }, [fetchUsers, search]);

  const toggleBan = async (userId: number) => {
    setBanLoading(userId);
    try {
      await fetch(`/api/users/${userId}/ban`, { method: 'PATCH', headers });
      await fetchUsers();
    } finally { setBanLoading(null); }
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-bold text-slate-100">Usuarios</h1>
          <p className="text-sm text-slate-500 mt-0.5">Gestión de usuarios del bot</p>
        </div>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-3 gap-4">
        {[
          { label: 'Total', value: stats.total ?? 0, color: 'text-slate-100' },
          { label: 'Activos', value: stats.active ?? 0, color: 'text-emerald-400' },
          { label: 'Baneados', value: stats.banned ?? 0, color: 'text-red-400' },
        ].map(({ label, value, color }) => (
          <div key={label} className="card text-center py-4">
            <p className={`text-2xl font-bold ${color}`}>{value}</p>
            <p className="text-sm text-slate-500">{label}</p>
          </div>
        ))}
      </div>

      {/* Search */}
      <div className="relative">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-500" />
        <input
          type="text"
          placeholder="Buscar por nombre o username..."
          value={search}
          onChange={e => setSearch(e.target.value)}
          className="w-full bg-surface-900 border border-surface-800 rounded-xl pl-10 pr-4 py-2.5 text-sm text-slate-300 placeholder-slate-600 focus:outline-none focus:border-brand-500 transition-colors"
        />
      </div>

      {/* Table */}
      <div className="card p-0 overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead>
              <tr className="border-b border-surface-800">
                <th className="th">Usuario</th>
                <th className="th">Telegram ID</th>
                <th className="th">Estado</th>
                <th className="th">Jobs</th>
                <th className="th">Registrado</th>
                <th className="th">Última vez</th>
                <th className="th">Acción</th>
              </tr>
            </thead>
            <tbody>
              {loading ? (
                <tr><td colSpan={7} className="td text-center py-12">
                  <div className="w-6 h-6 border-2 border-brand-500 border-t-transparent rounded-full animate-spin mx-auto" />
                </td></tr>
              ) : users.length === 0 ? (
                <tr><td colSpan={7} className="td text-center text-slate-600 py-12">No hay usuarios</td></tr>
              ) : users.map((user: any) => (
                <tr key={user.id} className="table-row">
                  <td className="td">
                    <div className="flex items-center gap-2.5">
                      <div className="w-8 h-8 rounded-full bg-brand-600/20 border border-brand-600/30 flex items-center justify-center flex-shrink-0">
                        <span className="text-xs font-bold text-brand-400">
                          {user.first_name?.[0]?.toUpperCase() || '?'}
                        </span>
                      </div>
                      <div>
                        <div className="text-sm text-slate-200">
                          {user.first_name} {user.last_name || ''}
                        </div>
                        {user.username && (
                          <div className="text-xs text-slate-500">@{user.username}</div>
                        )}
                      </div>
                    </div>
                  </td>
                  <td className="td font-mono text-xs text-slate-500">{user.telegram_id}</td>
                  <td className="td">
                    {user.is_banned
                      ? <span className="badge-red">baneado</span>
                      : user.is_active
                        ? <span className="badge-green">activo</span>
                        : <span className="badge-gray">inactivo</span>}
                  </td>
                  <td className="td">
                    <div className="flex items-center gap-1 text-sm">
                      <Briefcase className="w-3.5 h-3.5 text-slate-500" />
                      {user.job_count}
                    </div>
                  </td>
                  <td className="td text-xs text-slate-500">
                    {formatDistanceToNow(new Date(user.created_at), { addSuffix: true, locale: es })}
                  </td>
                  <td className="td text-xs text-slate-500">
                    {user.last_seen
                      ? formatDistanceToNow(new Date(user.last_seen), { addSuffix: true, locale: es })
                      : '—'}
                  </td>
                  <td className="td">
                    <button
                      onClick={() => toggleBan(user.id)}
                      disabled={banLoading === user.id}
                      className={`p-1.5 rounded transition-colors ${
                        user.is_banned
                          ? 'text-slate-400 hover:text-emerald-400 hover:bg-emerald-500/10'
                          : 'text-slate-400 hover:text-red-400 hover:bg-red-500/10'
                      }`}
                      title={user.is_banned ? 'Desbanear' : 'Banear'}
                    >
                      {banLoading === user.id
                        ? <div className="w-3.5 h-3.5 border border-current border-t-transparent rounded-full animate-spin" />
                        : user.is_banned
                          ? <UserCheck className="w-3.5 h-3.5" />
                          : <UserX className="w-3.5 h-3.5" />}
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
