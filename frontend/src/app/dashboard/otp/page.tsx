'use client';
import { useEffect, useState, useRef, useCallback } from 'react';
import { Shield, Clock, CheckCircle, AlertTriangle, Send } from 'lucide-react';
import { useAuthStore } from '@/lib/store';
import { useWebSocket } from '@/hooks/useWebSocket';
import { formatDistanceToNow } from 'date-fns';
import { es } from 'date-fns/locale';

const STATUS_BADGE: Record<string, string> = {
  pending:  'badge-red',
  resolved: 'badge-green',
  expired:  'badge-gray',
};

interface OTPRequest {
  id: number;
  user_id: number;
  job_id: number;
  status: 'pending' | 'resolved' | 'expired';
  screenshot_path: string | null;
  context_data: string | null;
  otp_value: string | null;
  resolved_by: string | null;
  resolved_at: string | null;
  created_at: string;
}

export default function OTPPage() {
  const { token } = useAuthStore();
  const { lastMessage } = useWebSocket();
  const [otps, setOtps] = useState<OTPRequest[]>([]);
  const [loading, setLoading] = useState(true);
  const [resolving, setResolving] = useState<number | null>(null);
  const [otpInputs, setOtpInputs] = useState<Record<number, string>>({});
  const [filter, setFilter] = useState<'all' | 'pending' | 'resolved'>('all');
  const [selectedOtp, setSelectedOtp] = useState<OTPRequest | null>(null);
  const audioRef = useRef<HTMLAudioElement | null>(null);

  const headers = { Authorization: `Bearer ${token}` };

  const fetchOTPs = useCallback(async () => {
    try {
      const params = filter !== 'all' ? `?status=${filter}&limit=50` : '?limit=50';
      const res = await fetch(`/api/otp/${params}`, { headers });
      const data = await res.json();
      setOtps(data);
    } catch (e) { console.error(e); }
    finally { setLoading(false); }
  }, [token, filter]);

  useEffect(() => { fetchOTPs(); }, [fetchOTPs]);

  // Real-time: play alert on new OTP
  useEffect(() => {
    if (lastMessage?.type === 'otp_required') {
      fetchOTPs();
      // Flash title
      document.title = '🔐 OTP REQUERIDA — CitaMonitor';
      setTimeout(() => { document.title = 'CitaMonitor — Admin Dashboard'; }, 5000);
    }
  }, [lastMessage, fetchOTPs]);

  const resolveOTP = async (otpId: number) => {
    const value = otpInputs[otpId]?.trim();
    if (!value) return;
    setResolving(otpId);
    try {
      const res = await fetch(`/api/otp/${otpId}/resolve`, {
        method: 'POST',
        headers: { ...headers, 'Content-Type': 'application/json' },
        body: JSON.stringify({ otp_value: value }),
      });
      if (res.ok) {
        setOtpInputs(prev => { const n = { ...prev }; delete n[otpId]; return n; });
        await fetchOTPs();
      }
    } finally { setResolving(null); }
  };

  const pendingCount = otps.filter(o => o.status === 'pending').length;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-bold text-slate-100 flex items-center gap-2">
            <Shield className="w-5 h-5 text-brand-400" />
            OTP Panel
          </h1>
          <p className="text-sm text-slate-500 mt-0.5">Gestión de códigos de verificación en tiempo real</p>
        </div>
        {pendingCount > 0 && (
          <div className="flex items-center gap-2 bg-red-500/10 border border-red-500/30 text-red-400 px-4 py-2 rounded-xl animate-pulse-slow">
            <AlertTriangle className="w-4 h-4" />
            <span className="font-semibold">{pendingCount} pendiente{pendingCount > 1 ? 's' : ''}</span>
          </div>
        )}
      </div>

      {/* Filter */}
      <div className="flex gap-2">
        {(['all', 'pending', 'resolved'] as const).map(f => (
          <button
            key={f}
            onClick={() => setFilter(f)}
            className={`px-4 py-1.5 rounded-lg text-sm font-medium transition-colors ${
              filter === f ? 'bg-brand-600 text-white' : 'text-slate-400 hover:text-slate-200 hover:bg-surface-800'
            }`}
          >
            {f === 'all' ? 'Todos' : f === 'pending' ? 'Pendientes' : 'Resueltos'}
          </button>
        ))}
      </div>

      {/* OTP cards */}
      {loading ? (
        <div className="flex items-center justify-center h-40">
          <div className="w-6 h-6 border-2 border-brand-500 border-t-transparent rounded-full animate-spin" />
        </div>
      ) : otps.length === 0 ? (
        <div className="card text-center py-16">
          <CheckCircle className="w-10 h-10 text-emerald-400 mx-auto mb-3" />
          <p className="text-slate-400 font-medium">Sin OTPs pendientes</p>
          <p className="text-slate-600 text-sm mt-1">Todo en orden</p>
        </div>
      ) : (
        <div className="space-y-3">
          {otps.map((otp) => (
            <div
              key={otp.id}
              className={`card transition-all ${
                otp.status === 'pending'
                  ? 'border-red-500/30 bg-red-950/20 hover:border-red-500/50'
                  : 'opacity-60 hover:opacity-80'
              }`}
            >
              <div className="flex flex-col sm:flex-row sm:items-start gap-4">
                {/* Left: info */}
                <div className="flex-1 space-y-2">
                  <div className="flex items-center gap-3 flex-wrap">
                    <span className={STATUS_BADGE[otp.status]}>{otp.status}</span>
                    <span className="text-xs font-mono text-slate-500">OTP #{otp.id}</span>
                    <span className="text-xs text-slate-600 flex items-center gap-1">
                      <Clock className="w-3 h-3" />
                      {formatDistanceToNow(new Date(otp.created_at), { addSuffix: true, locale: es })}
                    </span>
                  </div>
                  <div className="grid grid-cols-2 gap-x-6 gap-y-1 text-sm">
                    <div className="text-slate-500">Job ID</div>
                    <div className="text-slate-300 font-mono">#{otp.job_id}</div>
                    <div className="text-slate-500">Usuario ID</div>
                    <div className="text-slate-300 font-mono">#{otp.user_id}</div>
                    {otp.resolved_by && <>
                      <div className="text-slate-500">Resuelto por</div>
                      <div className="text-slate-300">{otp.resolved_by}</div>
                    </>}
                    {otp.otp_value && <>
                      <div className="text-slate-500">Código usado</div>
                      <div className="text-emerald-400 font-mono">{otp.otp_value}</div>
                    </>}
                  </div>
                  {otp.screenshot_path && (
                    <button
                      onClick={() => setSelectedOtp(otp)}
                      className="text-xs text-brand-400 hover:text-brand-300 underline"
                    >
                      Ver screenshot →
                    </button>
                  )}
                </div>

                {/* Right: input (only for pending) */}
                {otp.status === 'pending' && (
                  <div className="flex-shrink-0 w-full sm:w-56">
                    <label className="block text-xs text-slate-500 mb-1.5">Código OTP</label>
                    <div className="flex gap-2">
                      <input
                        type="text"
                        placeholder="Ej. 123456"
                        value={otpInputs[otp.id] || ''}
                        onChange={e => setOtpInputs(prev => ({ ...prev, [otp.id]: e.target.value }))}
                        onKeyDown={e => e.key === 'Enter' && resolveOTP(otp.id)}
                        className="flex-1 bg-surface-800 border border-surface-700 rounded-lg px-3 py-2 text-sm text-slate-100 font-mono focus:outline-none focus:border-brand-500 placeholder-slate-600 transition-colors"
                        autoFocus={otp.status === 'pending'}
                      />
                      <button
                        onClick={() => resolveOTP(otp.id)}
                        disabled={resolving === otp.id || !otpInputs[otp.id]?.trim()}
                        className="btn-primary px-3 disabled:opacity-40"
                        title="Enviar OTP"
                      >
                        {resolving === otp.id
                          ? <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
                          : <Send className="w-4 h-4" />}
                      </button>
                    </div>
                    <p className="text-xs text-slate-600 mt-1">Enter para confirmar</p>
                  </div>
                )}
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Screenshot modal */}
      {selectedOtp?.screenshot_path && (
        <div className="fixed inset-0 bg-black/80 z-50 flex items-center justify-center p-4" onClick={() => setSelectedOtp(null)}>
          <div className="max-w-2xl w-full animate-slide-up" onClick={e => e.stopPropagation()}>
            <div className="bg-surface-900 border border-surface-700 rounded-xl overflow-hidden">
              <div className="flex items-center justify-between px-4 py-3 border-b border-surface-800">
                <span className="text-sm font-medium text-slate-300">Screenshot — OTP #{selectedOtp.id}</span>
                <button onClick={() => setSelectedOtp(null)} className="text-slate-500 hover:text-slate-300 text-xl leading-none">×</button>
              </div>
              <img
                src={`/screenshots/${selectedOtp.screenshot_path.split('/').pop()}`}
                className="w-full"
                alt="OTP screenshot"
              />
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
