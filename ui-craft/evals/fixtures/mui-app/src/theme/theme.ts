import { createTheme } from '@mui/material/styles';

export const theme = createTheme({
  cssVariables: { colorSchemeSelector: 'class' },
  colorSchemes: {
    light: {
      palette: {
        primary: { main: '#0f766e' },
        secondary: { main: '#b45309' },
        background: { default: '#f7f5f0', paper: '#ffffff' },
      },
    },
    dark: {
      palette: {
        primary: { main: '#5eead4' },
        background: { default: '#14120f', paper: '#1d1a16' },
      },
    },
  },
  shape: { borderRadius: 10 },
  typography: { fontFamily: '"Inter", system-ui, sans-serif' },
  components: {
    MuiButton: { styleOverrides: { root: { textTransform: 'none' } } },
  },
});
