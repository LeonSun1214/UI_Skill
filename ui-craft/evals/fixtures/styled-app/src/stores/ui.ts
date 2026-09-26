const THEME_STORAGE_KEY = 'theme';

export function useThemeChoice(): 'light' | 'dark' {
  return localStorage.getItem(THEME_STORAGE_KEY) === 'dark' ? 'dark' : 'light';
}
