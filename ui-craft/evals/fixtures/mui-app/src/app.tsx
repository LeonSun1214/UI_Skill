import type { ReactNode } from 'react';
import { ThemeProvider } from './theme/theme-provider';

export default function App({ children }: { children: ReactNode }) {
  return <ThemeProvider>{children}</ThemeProvider>;
}
