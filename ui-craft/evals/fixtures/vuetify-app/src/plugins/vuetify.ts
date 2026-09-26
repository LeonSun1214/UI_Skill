import 'vuetify/styles';
import { createVuetify } from 'vuetify';

export default createVuetify({
  theme: {
    defaultTheme: 'light',
    themes: {
      light: {
        dark: false,
        colors: { primary: '#00695c', secondary: '#6d4c41', surface: '#ffffff', background: '#f6f4ef', error: '#b3261e' },
      },
      dark: {
        dark: true,
        colors: { primary: '#4db6ac', secondary: '#bcaaa4', surface: '#1e1e1e', background: '#121212' },
      },
    },
  },
  defaults: {
    VBtn: { variant: 'flat', rounded: 'lg' },
    VCard: { rounded: 'xl', elevation: 0 },
    VTextField: { variant: 'outlined', density: 'comfortable' },
  },
});
