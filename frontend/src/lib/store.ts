import { create } from 'zustand';
import { persist } from 'zustand/middleware';

interface AuthState {
  token: string | null;
  setToken: (token: string) => void;
  logout: () => void;
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      token: null,
      setToken: (token) => set({ token }),
      logout: () => {
        set({ token: null });
        if (typeof window !== 'undefined') localStorage.removeItem('token');
      },
    }),
    { name: 'citamonitor-auth' }
  )
);

// API helper
export const api = {
  async get(path: string, token?: string | null) {
    const res = await fetch(path.startsWith('/api') ? path : `/api${path}`, {
      headers: token ? { Authorization: `Bearer ${token}` } : {},
    });
    if (!res.ok) throw new Error(`API error: ${res.status}`);
    return res.json();
  },

  async post(path: string, body: any, token?: string | null) {
    const res = await fetch(path.startsWith('/api') ? path : `/api${path}`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
      },
      body: JSON.stringify(body),
    });
    if (!res.ok) throw new Error(`API error: ${res.status}`);
    return res.json();
  },

  async patch(path: string, body: any, token?: string | null) {
    const res = await fetch(path.startsWith('/api') ? path : `/api${path}`, {
      method: 'PATCH',
      headers: {
        'Content-Type': 'application/json',
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
      },
      body: JSON.stringify(body),
    });
    if (!res.ok) throw new Error(`API error: ${res.status}`);
    return res.json();
  },
};
