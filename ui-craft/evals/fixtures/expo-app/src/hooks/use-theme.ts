import { Colors } from '@/constants/theme';
import { useAppScheme } from '@/hooks/use-app-scheme';

export function useTheme() {
  return Colors[useAppScheme()];
}
