'use client';
import { useEffect, useRef, useState, useCallback } from 'react';
import { useAuthStore } from '@/lib/store';

interface WSMessage {
  type: string;
  data?: any;
  channel?: string;
  [key: string]: any;
}

export function useWebSocket() {
  const { token } = useAuthStore();
  const ws = useRef<WebSocket | null>(null);
  const [connected, setConnected] = useState(false);
  const [lastMessage, setLastMessage] = useState<WSMessage | null>(null);
  const reconnectTimer = useRef<NodeJS.Timeout>();
  const retries = useRef(0);

  const connect = useCallback(() => {
    if (!token || typeof window === 'undefined') return;

    const wsUrl = process.env.NEXT_PUBLIC_WS_URL || 'ws://localhost/ws';
    const url = `${wsUrl}/admin?token=${token}`;

    try {
      ws.current = new WebSocket(url);

      ws.current.onopen = () => {
        setConnected(true);
        retries.current = 0;
        console.log('[WS] Connected');
      };

      ws.current.onmessage = (event) => {
        try {
          const msg = JSON.parse(event.data);
          setLastMessage(msg);
        } catch {}
      };

      ws.current.onclose = () => {
        setConnected(false);
        // Exponential backoff reconnect
        const delay = Math.min(30000, 1000 * 2 ** retries.current);
        retries.current += 1;
        reconnectTimer.current = setTimeout(connect, delay);
      };

      ws.current.onerror = () => {
        ws.current?.close();
      };
    } catch (err) {
      console.error('[WS] Error:', err);
    }
  }, [token]);

  useEffect(() => {
    connect();
    return () => {
      clearTimeout(reconnectTimer.current);
      ws.current?.close();
    };
  }, [connect]);

  const send = useCallback((data: any) => {
    if (ws.current?.readyState === WebSocket.OPEN) {
      ws.current.send(JSON.stringify(data));
    }
  }, []);

  // Heartbeat
  useEffect(() => {
    const interval = setInterval(() => {
      send({ type: 'ping' });
    }, 25000);
    return () => clearInterval(interval);
  }, [send]);

  return { connected, lastMessage, send };
}
