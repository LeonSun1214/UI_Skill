import { useColorScheme } from 'react-native';
import { useMMKVString } from 'react-native-mmkv';

import { storage } from '@/lib/storage';

export function useSchemeChoice() {
  return useMMKVString('app.colorScheme', storage);
}

export function useAppScheme(): 'light' | 'dark' {
  const device = useColorScheme();
  const [choice] = useSchemeChoice();
  const scheme = choice ?? device;
  return scheme === 'dark' ? 'dark' : 'light';
}
