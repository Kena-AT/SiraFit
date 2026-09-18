import { useEffect, useRef, useState } from "react";

export function useWebSocket(url: string, fallbackPoll: () => void) {
  const [lastMessage, setLastMessage] = useState<any>(null);
  const [isConnected, setIsConnected] = useState<boolean>(false);
  const wsRef = useRef<WebSocket | null>(null);

  useEffect(() => {
    let ws: WebSocket | null = null;
    let reconnectTimer: number;
    let reconnectAttempts = 0;
    const maxReconnectDelay = 30000;

    const connect = () => {
      try {
        ws = new WebSocket(url);
        wsRef.current = ws;

        ws.onopen = () => {
          console.log("WebSocket connected");
          setIsConnected(true);
          reconnectAttempts = 0;
          // Refetch on reconnect to catch missed events
          fallbackPoll();
        };

        ws.onmessage = (event) => {
          try {
            const data = JSON.parse(event.data);
            setLastMessage(data);
          } catch (e) {
            console.error("Failed to parse WS message", e);
          }
        };

        ws.onerror = () => {
          console.warn("WebSocket error, falling back to polling");
          setIsConnected(false);
          fallbackPoll();
        };

        ws.onclose = (event) => {
          console.warn(`WebSocket disconnected (code: ${event.code}), reconnecting...`);
          setIsConnected(false);
          fallbackPoll();

          // Exponential backoff
          const delay = Math.min(1000 * Math.pow(2, reconnectAttempts), maxReconnectDelay);
          reconnectAttempts++;
          reconnectTimer = window.setTimeout(connect, delay);
        };
      } catch (e) {
        console.error("WebSocket init failed", e);
        fallbackPoll();
      }
    };

    connect();

    return () => {
      clearTimeout(reconnectTimer);
      if (ws) {
        ws.onclose = null; // Prevent reconnect on intentional unmount
        ws.close();
      }
    };
  }, [url, fallbackPoll]);

  return lastMessage;
}
