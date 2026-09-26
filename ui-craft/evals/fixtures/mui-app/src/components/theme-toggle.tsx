import IconButton from '@mui/material/IconButton';
import { useColorScheme } from '@mui/material/styles';

export function ThemeToggle() {
  const { mode, setMode } = useColorScheme();
  return (
    <IconButton aria-label="Toggle dark mode" onClick={() => setMode(mode === 'dark' ? 'light' : 'dark')}>
      {mode === 'dark' ? '☀' : '☾'}
    </IconButton>
  );
}
