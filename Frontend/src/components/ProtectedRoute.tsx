import { useEffect, useRef } from "react";
import type { ReactNode } from "react";
import { Navigate, useLocation } from "react-router-dom";
import { useAuth } from "@/hooks/AuthContext";

const ProtectedRoute = ({ children }: { children: ReactNode }) => {
  const { isAuthenticated, isLoading, refreshAuth } = useAuth();
  const location = useLocation();
  const hasAuthedOnce = useRef(false);

  if (isAuthenticated) {
    hasAuthedOnce.current = true;
  }

  // Soft re-check on navigation — never flip global loading / unmount chat
  useEffect(() => {
    if (!hasAuthedOnce.current) return;
    refreshAuth({ silent: true });
  }, [location.pathname, refreshAuth]);

  // Only block the first auth check; later path changes keep children mounted
  if (isLoading && !hasAuthedOnce.current) {
    return (
      <div className="flex h-screen items-center justify-center bg-background">
        <div className="w-8 h-8 border-2 border-primary/30 border-t-primary rounded-full animate-spin" />
      </div>
    );
  }

  if (!isAuthenticated && !isLoading) {
    return <Navigate to="/auth" replace state={{ from: location.pathname }} />;
  }

  if (!isAuthenticated) {
    return (
      <div className="flex h-screen items-center justify-center bg-background">
        <div className="w-8 h-8 border-2 border-primary/30 border-t-primary rounded-full animate-spin" />
      </div>
    );
  }

  return <>{children}</>;
};

export default ProtectedRoute;
