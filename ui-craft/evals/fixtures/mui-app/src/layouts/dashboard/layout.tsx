import type { ReactNode } from 'react';
import Box from '@mui/material/Box';
import AppBar from '@mui/material/AppBar';
import Toolbar from '@mui/material/Toolbar';
import Typography from '@mui/material/Typography';
import { ThemeToggle } from 'src/components/theme-toggle';

export function DashboardLayout({ children }: { children: ReactNode }) {
  return (
    <Box sx={{ display: 'flex', flexDirection: 'column', minHeight: '100vh' }}>
      <AppBar position="static" color="default">
        <Toolbar>
          <Typography variant="h6" sx={{ flexGrow: 1 }}>Harbor</Typography>
          <ThemeToggle />
        </Toolbar>
      </AppBar>
      <Box component="main" sx={{ p: 3 }}>{children}</Box>
    </Box>
  );
}
