import type { ReactNode } from 'react';
import { Navigate } from 'react-router';

export function RequireAuth({ children }: { children: ReactNode }) {
  return localStorage.getItem('mui-app-session') ? <>{children}</> : <Navigate to="/sign-in" />;
}
