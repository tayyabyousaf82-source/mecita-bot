'use client';
import { useEffect, useState, useRef, useCallback } from 'react';
import { Terminal, RefreshCw, Filter } from 'lucide-react';
import { useAuthStore } from '@/lib/store';
import { useWebSocket } from '@/hooks/useWebSocket';
import { formatDistanceToNow } from 'date-fns';
import { es } from 'date-fns/locale';

const LEVEL_STYLES: Record<string, string> = {
  debug:   'text-slate-500',
  info:    'text-blue-400',
  warning: 'text-amber-400',
  error:   'text-red-400',
};
const LEVEL_BADGE: Record<string, string> = {
  debug:   'badge-gray',
  info:    'badge-blue',
  warning: 'badge-yellow',
  error:   'badge-red',
};
const SOURCES = ['all', 'playwright', 'bot', 'system', 'worker'];
const LEVELS  = ['all', 'debug', 'info', 'warning', 'error'];

export default function LogsPage() {
  const { token } = useAuthStore();
  const { lastMessage } = useWebSocket();
  const [logs, setLogs] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [autoScroll, setAutoScroll] = useState(true);
  const [source, setSource] = useState('all');
  const [level, setLevel]   = useState('all');
  const bottomRef = useRef<HTMLDivElement>(null);
  const headers = { Authorization: `Bearer ${token}` };

  const fetchLogs = useCallback(async () => {
    try {
      const params = new URLSearchParams({ limit: '200' });
      if (source !== 'all') params.set('source', source);
      if (level  !== 'all') params.set('level', level);
      const res = await fetch(`/api/logs/?${params}`, { headers });
      const data = await res.json();
      setLogs(data.reverse()); // chronological order
    } catch (e) { console.error(e); }
    finally { setLoading(false); }
  }, [token, source, level]);

  useEffect(() => { fetchLogs(); }, [fetchLogs]);

  // Auto-refresh on WS
  useEffect(() => {
    if (lastMessage?.type === 'log') fetchLogs();
  }, [lastMessage, fetchLogs]);

  // Periodic refresh
  useEffect(() => {
    const t = setInterval(fetchLogs, 5000);
    return () => clearInterval(t);
  }, [fetchLogs]);

  useEffect(() => {
    if (autoScroll) bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [logs, autoScroll]);

  return (
    <div className="space-y-4 h-[calc(100vh-8rem)] flex flex-col">
      {/* Header */}
      <div className="flex items-center justify-between flex-shrink-0">
        <div>
          <h1 className="text-xl font-bold text-slate-100 flex items-center gap-2">
            <Terminal className="w-5 h-5 text-brand-400" />
            Logs del Sistema
          </h1>
          <p className="text-sm text-slate-500 mt-0.5">Stream en tiempo real — {logs.length} entradas</p>
        </div>
        <div className="flex items-center gap-2">
          <label className="flex items-center gap-2 text-xs text-slate-500 cursor-pointer">
            <input
              type="checkbox"
              checked={autoScroll}
              onChange={e => setAutoScroll(e.target.checked)}
              className="w-3 h-3"
            />
            Auto-scroll
          </label>
          <button onClick={fetchLogs} className="btn-ghost p-2" title="Refrescar">
            <RefreshCw className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* Filters */}
      <div className="card py-2.5 px-4 flex flex-wrap gap-4 items-center flex-shrink-0">
        <div className="flex items-center gap-2">
          <Filter className="w-3.5 h-3.5 text-slate-500" />
          <span className="text-xs text-slate-500">Fuente:</span>
          {SOURCES.map(s => (
            <button key={s} onClick={() => setSource(s)}
              className={`px-2.5 py-1 rounded text-xs font-medium transition-colors ${
                source === s ? 'bg-brand-600 text-white' : 'text-slate-400 hover:text-slate-200 hover:bg-surface-800'
              }`}>
              {s}
            </button>
          ))}
        </div>
        <div className="flex items-center gap-2">
          <span className="text-xs text-slate-500">Nivel:</span>
          {LEVELS.map(l => (
            <button key={l} onClick={() => setLevel(l)}
              className={`px-2.5 py-1 rounded text-xs font-medium transition-colors ${
                level === l ? 'bg-brand-600 text-white' : 'text-slate-400 hover:text-slate-200 hover:bg-surface-800'
              }`}>
              {l}
            </button>
          ))}
        </div>
      </div>

      {/* Log terminal */}
      <div className="flex-1 card p-0 overflow-hidden flex flex-col min-h-0">
        <div className="flex items-center gap-2 px-4 py-2 border-b border-surface-800 bg-surface-950 flex-shrink-0">
          <div className="flex gap-1.5">
            <div className="w-2.5 h-2.5 rounded-full bg-red-500" />
            <div className="w-2.5 h-2.5 rounded-full bg-amber-500" />
            <div className="w-2.5 h-2.5 rounded-full bg-emerald-500" />
          </div>
          <span className="text-xs text-slate-600 font-mono ml-2">citamonitor — system logs</span>
        </div>

        <div className="flex-1 overflow-y-auto p-4 font-mono text-xs space-y-0.5">
          {loading ? (
            <div className="flex items-center gap-2 text-slate-600">
              <div className="w-4 h-4 border border-slate-600 border-t-transparent rounded-full animate-spin" />
              Cargando logs...
            </div>
          ) : logs.length === 0 ? (
            <div className="text-slate-600">No hay logs con el filtro seleccionado.</div>
          ) : logs.map((log: any) => (
            <div key={log.id} className="flex items-start gap-3 hover:bg-surface-800/50 px-2 py-0.5 rounded group">
              <span className="text-slate-700 flex-shrink-0 select-none">
                {new Date(log.created_at).toLocaleTimeString('es-ES')}
              </span>
              <span className={`flex-shrink-0 w-14 ${LEVEL_STYLES[log.level] || 'text-slate-400'}`}>
                [{log.level?.toUpperCase()}]
              </span>
              <span className="text-slate-600 flex-shrink-0 w-20">{log.source}</span>
              <span className={`flex-1 ${log.level === 'error' ? 'text-red-300' : log.level === 'warning' ? 'text-amber-300' : 'text-slate-300'}`}>
                {log.message}
              </span>
              {log.job_id && (
                <span className="text-slate-700 flex-shrink-0 opacity-0 group-hover:opacity-100 transition-opacity">
                  job#{log.job_id}
                </span>
              )}
            </div>
          ))}
          <div ref={bottomRef} />
        </div>
      </div>
    </div>
  );
}
