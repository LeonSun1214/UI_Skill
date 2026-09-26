import type { DefaultTheme } from 'styled-components';

const colors = {
  accent: '#0b6bcb',
  danger: '#c62828',
  text: '#1b1f24',
  textSecondary: '#5b6470',
  background: '#ffffff',
  backgroundSecondary: '#f3f5f8',
  divider: '#dde2e8',
};

export const lightTheme: DefaultTheme = { ...colors };

export const darkTheme: DefaultTheme = {
  ...colors,
  accent: '#6cb4ff',
  text: '#e6e9ee',
  textSecondary: '#a3acb8',
  background: '#111418',
  backgroundSecondary: '#1a1f25',
  divider: '#2b323b',
};
