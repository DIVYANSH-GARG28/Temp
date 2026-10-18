import { useEffect, useState, type ReactNode } from "react";
import { Navigate, useLocation } from "react-router-dom";
import { hasAccessToken, SESSION_EXPIRED_EVENT } from "../services/api";

export function RequireAuth({ children }: { children: ReactNode }) {
  const location = useLocation();
  const [authenticated, setAuthenticated] = useState(hasAccessToken);

  useEffect(() => {
    function handleSessionExpired() {
      setAuthenticated(false);
    }

    window.addEventListener(SESSION_EXPIRED_EVENT, handleSessionExpired);
    return () =>
      window.removeEventListener(SESSION_EXPIRED_EVENT, handleSessionExpired);
  }, []);

  if (!authenticated || !hasAccessToken()) {
    return (
      <Navigate
        to="/login"
        replace
        state={{ from: location.pathname + location.search + location.hash }}
      />
    );
  }

  return children;
}
