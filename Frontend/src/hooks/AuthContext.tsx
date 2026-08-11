import { createContext, useCallback, useContext, useEffect, useRef, useState } from "react";
import type { ReactNode } from "react";

const API_BASE = import.meta.env.VITE_API_URL || "http://localhost:8000";
const AUTH_TIMEOUT_MS = 15000;

async function fetchWithTimeout(
  input: RequestInfo | URL,
  init: RequestInit = {},
  timeoutMs = AUTH_TIMEOUT_MS,
): Promise<Response> {
  const controller = new AbortController();
  const timeoutId = window.setTimeout(() => controller.abort(), timeoutMs);
  try {
    return await fetch(input, {
      ...init,
      signal: controller.signal,
    });
  } finally {
    window.clearTimeout(timeoutId);
  }
}

export interface CurrentUser {
  id: number;
  email: string;
  is_active?: boolean;
  created_at?: string;
}

interface AuthContextType {
  isAuthenticated: boolean;
  isLoading: boolean;
  user: CurrentUser | null;
  logout: () => Promise<void>;
  refreshAuth: (options?: { silent?: boolean }) => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [isLoading, setIsLoading] = useState(true);
  const [user, setUser] = useState<CurrentUser | null>(null);
  const authInFlightRef = useRef(false);
  const lastAuthWarnRef = useRef(0);

  const checkAuth = useCallback(async () => {
    if (authInFlightRef.current) return;
    authInFlightRef.current = true;
    try {
      const res = await fetchWithTimeout(`${API_BASE}/me`, {
        credentials: "include",
        cache: "no-store",
      });
      if (res.ok) {
        const data = await res.json();
        setIsAuthenticated(true);
        setUser({
          id: data.id,
          email: data.email,
          is_active: data.is_active,
          created_at: data.created_at,
        });
      } else {
        setIsAuthenticated(false);
        setUser(null);
      }
    } catch (err) {
      if (err instanceof DOMException && err.name === "AbortError") {
        const now = Date.now();
        if (now - lastAuthWarnRef.current > 30000) {
          lastAuthWarnRef.current = now;
          console.warn("Auth check timed out — is the backend running?");
        }
      }
      setIsAuthenticated(false);
      setUser(null);
    } finally {
      authInFlightRef.current = false;
    }
  }, []);

  const refreshAuth = useCallback(async (options?: { silent?: boolean }) => {
    if (!options?.silent) {
      setIsLoading(true);
    }
    try {
      await checkAuth();
    } finally {
      if (!options?.silent) {
        setIsLoading(false);
      }
    }
  }, [checkAuth]);

  useEffect(() => {
    refreshAuth();
  }, [refreshAuth]);

  // Re-validate when returning via back/forward — debounced to avoid request storms
  useEffect(() => {
    let debounceTimer: ReturnType<typeof setTimeout> | null = null;

    const scheduleCheck = () => {
      if (debounceTimer) clearTimeout(debounceTimer);
      debounceTimer = setTimeout(() => {
        checkAuth();
      }, 1500);
    };

    window.addEventListener("pageshow", scheduleCheck);
    window.addEventListener("focus", scheduleCheck);
    return () => {
      if (debounceTimer) clearTimeout(debounceTimer);
      window.removeEventListener("pageshow", scheduleCheck);
      window.removeEventListener("focus", scheduleCheck);
    };
  }, [checkAuth]);

  const logout = async () => {
    try {
      await fetch(`${API_BASE}/logout`, {
        method: "POST",
        credentials: "include",
        cache: "no-store",
      });
    } catch (err) {
      console.error("Logout failed:", err);
    } finally {
      setIsAuthenticated(false);
      setUser(null);
      window.location.replace("/auth");
    }
  };

  return (
    <AuthContext.Provider value={{ isAuthenticated, isLoading, user, logout, refreshAuth }}>
      {children}
    </AuthContext.Provider>
  );
}

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) throw new Error("useAuth must be used within AuthProvider");
  return context;
};
