'use client';
import { useEffect, useState, useCallback } from 'react';
import { Square, RotateCcw, Eye, Search, Filter } from 'lucide-react';
import { useAuthStore } from '@/lib/store';
import { useWebSocket } from '@/hooks/useWebSocket';
import { formatDistanceToNow } from 'date-fns';
import { es } from 'date-fns/locale';

const STATUS_BADGE: Record<string, string> = {
  searching: 'badge-blue',
  found:     'badge-green',
  stopped:   'badge-gray',
  error:     'badge-red',
  queued:    'badge-yellow',
  paused:    'badge-yellow',
};

const STATUSES = ['all', 'searching', 'queued', 'found', 'stopped', 'error', 'paused'];

export default function JobsPage() {
  const { token } = useAuthStore();
  const { lastMessage } = useWebSocket();
  const [jobs, setJobs] = useState<any[]>([]);
  const [stats, setStats] = useState<any>({});
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState('all');
  const [actionLoading, setActionLoading] = useState<number | null>(null);
  const [selectedJob, setSelectedJob] = useState<any | null>(null);

  const headers = { Authorization: `Bearer ${token}` };

  const fetchJobs = useCallback(async () => {
    try {
      const params = filter !== 'all' ? `?status=${filter}&limit=100` : '?limit=100';
      const [jobsRes, statsRes] = await Promise.all([
        fetch(`/api/jobs/${params}`, { headers }),
        fetch('/api/jobs/stats', { headers }),
      ]);
      setJobs(await jobsRes.json());
      setStats(await statsRes.json());
    } catch (e) { console.error(e); }
    finally { setLoading(false); }
  }, [token, filter]);

  useEffect(() => { fetchJobs(); }, [fetchJobs]);

  useEffect(() => {
    if (lastMessage?.type === 'job_update') fetchJobs();
  }, [lastMessage, fetchJobs]);

  const stopJob = async (jobId: number) => {
    setActionLoading(jobId);
    try {
      await fetch(`/api/jobs/${jobId}/stop`, { method: 'POST', headers });
      await fetchJobs();
    } finally { setActionLoading(null); }
  };

  const restartJob = async (jobId: number) => {
    setActionLoading(jobId);
    try {
      await fetch(`/api/jobs/${jobId}/restart`, { method: 'POST', headers });
      await fetchJobs();
    } finally { setActionLoading(null); }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-bold text-slate-100">Monitoring Jobs</h1>
          <p className="text-sm text-slate-500 mt-0.5">Gestión de sesiones de monitoreo</p>
        </div>
      </div>

      {/* Stats row */}
      <div className="grid grid-cols-3 sm:grid-cols-6 gap-3">
        {['searching', 'queued', 'found', 'stopped', 'error', 'paused'].map(s => (
          <div key={s} className="card py-3 text-center">
            <p className="text-lg font-bold text-slate-100">{stats[s] ?? 0}</p>
            <span className={STATUS_BADGE[s]}>{s}</span>
          </div>
        ))}
      </div>

      {/* Filter bar */}
      <div className="card py-3 px-4 flex flex-wrap gap-2 items-center">
        <Filter className="w-4 h-4 text-slate-500" />
        {STATUSES.map(s => (
          <button
            key={s}
            onClick={() => setFilter(s)}
            className={`px-3 py-1 rounded-lg text-xs font-medium transition-colors ${
              filter === s
                ? 'bg-brand-600 text-white'
                : 'text-slate-400 hover:text-slate-200 hover:bg-surface-800'
            }`}
          >
            {s === 'all' ? 'Todos' : s}
          </button>
        ))}
        <span className="ml-auto text-xs text-slate-600">{jobs.length} resultados</span>
      </div>

      {/* Table */}
      <div className="card p-0 overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead>
              <tr className="border-b border-surface-800">
                <th className="th">ID</th>
                <th className="th">Usuario</th>
                <th className="th">Provincia / Trámite</th>
                <th className="th">Estado</th>
                <th className="th">Checks</th>
                <th className="th">Último check</th>
                <th className="th">Errores</th>
                <th className="th">Acciones</th>
              </tr>
            </thead>
            <tbody>
              {loading ? (
                <tr><td colSpan={8} className="td text-center py-12">
                  <div className="w-6 h-6 border-2 border-brand-500 border-t-transparent rounded-full animate-spin mx-auto" />
                </td></tr>
              ) : jobs.length === 0 ? (
                <tr><td colSpan={8} className="td text-center text-slate-600 py-12">No hay jobs con este filtro</td></tr>
              ) : jobs.map((job: any) => (
                <tr key={job.id} className="table-row">
                  <td className="td font-mono text-slate-500 text-xs">#{job.id}</td>
                  <td className="td text-sm">{job.user_name || <span className="text-slate-600">—</span>}</td>
                  <td className="td">
                    <div className="text-sm">{job.province_name || '—'}</div>
                    <div className="text-xs text-slate-500 truncate max-w-[180px]">{job.tramite_name || '—'}</div>
                  </td>
                  <td className="td">
                    <span className={STATUS_BADGE[job.status] || 'badge-gray'}>{job.status}</span>
                  </td>
                  <td className="td font-mono text-sm">{job.check_count.toLocaleString()}</td>
                  <td className="td text-xs text-slate-500">
                    {job.last_check_at
                      ? formatDistanceToNow(new Date(job.last_check_at), { addSuffix: true, locale: es })
                      : '—'}
                  </td>
                  <td className="td">
                    {job.error_count > 0
                      ? <span className="badge-red">{job.error_count}</span>
                      : <span className="text-slate-600 text-xs">0</span>}
                  </td>
                  <td className="td">
                    <div className="flex items-center gap-1">
                      {job.status === 'searching' && (
                        <button
                          onClick={() => stopJob(job.id)}
                          disabled={actionLoading === job.id}
                          title="Detener"
                          className="p-1.5 text-slate-400 hover:text-red-400 hover:bg-red-500/10 rounded transition-colors"
                        >
                          <Square className="w-3.5 h-3.5" />
                        </button>
                      )}
                      {['stopped', 'error'].includes(job.status) && (
                        <button
                          onClick={() => restartJob(job.id)}
                          disabled={actionLoading === job.id}
                          title="Reiniciar"
                          className="p-1.5 text-slate-400 hover:text-emerald-400 hover:bg-emerald-500/10 rounded transition-colors"
                        >
                          <RotateCcw className="w-3.5 h-3.5" />
                        </button>
                      )}
                      <button
                        onClick={() => setSelectedJob(job)}
                        title="Ver detalles"
                        className="p-1.5 text-slate-400 hover:text-brand-400 hover:bg-brand-500/10 rounded transition-colors"
                      >
                        <Eye className="w-3.5 h-3.5" />
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Job detail modal */}
      {selectedJob && (
        <div className="fixed inset-0 bg-black/60 z-50 flex items-center justify-center p-4" onClick={() => setSelectedJob(null)}>
          <div className="card max-w-lg w-full space-y-4 animate-slide-up" onClick={e => e.stopPropagation()}>
            <div className="flex items-center justify-between">
              <h2 className="font-semibold text-slate-100">Job #{selectedJob.id}</h2>
              <span className={STATUS_BADGE[selectedJob.status]}>{selectedJob.status}</span>
            </div>
            <div className="space-y-2 text-sm">
              {[
                ['Usuario', selectedJob.user_name],
                ['Provincia', selectedJob.province_name],
                ['Trámite', selectedJob.tramite_name],
                ['Worker ID', selectedJob.worker_id || '—'],
                ['Total checks', selectedJob.check_count],
                ['Errores', selectedJob.error_count],
                ['Mensaje de error', selectedJob.error_message || '—'],
              ].map(([k, v]) => (
                <div key={String(k)} className="flex justify-between gap-4">
                  <span className="text-slate-500 flex-shrink-0">{k}</span>
                  <span className="text-slate-300 text-right truncate">{String(v)}</span>
                </div>
              ))}
            </div>
            {selectedJob.screenshot_path && (
              <div>
                <p className="text-xs text-slate-500 mb-2">Screenshot</p>
                <img
                  src={`/screenshots/${selectedJob.screenshot_path.split('/').pop()}`}
                  className="rounded-lg w-full border border-surface-700"
                  alt="screenshot"
                />
              </div>
            )}
            <button onClick={() => setSelectedJob(null)} className="btn-ghost w-full text-center text-sm">
              Cerrar
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
