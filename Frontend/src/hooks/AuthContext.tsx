import { createContext, useCallback, useContext, useEffect, useState } from "react";
import type { ReactNode } from "react";

const API_BASE = import.meta.env.VITE_API_URL || "http://localhost:8000";

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

  const checkAuth = useCallback(async () => {
    try {
      const res = await fetch(`${API_BASE}/me`, {
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
    } catch {
      setIsAuthenticated(false);
      setUser(null);
    }
  }, []);

  const refreshAuth = useCallback(async (options?: { silent?: boolean }) => {
    if (!options?.silent) {
      setIsLoading(true);
    }
    await checkAuth();
    if (!options?.silent) {
      setIsLoading(false);
    }
  }, [checkAuth]);

  useEffect(() => {
    refreshAuth();
  }, [refreshAuth]);

  // Re-validate when returning via back/forward (bfcache) or refocusing the tab
  useEffect(() => {
    const handlePageShow = () => {
      checkAuth();
    };
    const handleFocus = () => {
      checkAuth();
    };

    window.addEventListener("pageshow", handlePageShow);
    window.addEventListener("focus", handleFocus);
    return () => {
      window.removeEventListener("pageshow", handlePageShow);
      window.removeEventListener("focus", handleFocus);
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
