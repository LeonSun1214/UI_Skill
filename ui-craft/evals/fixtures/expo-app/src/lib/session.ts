import { useMMKVString } from 'react-native-mmkv';

import { storage } from '@/lib/storage';

const TOKEN_KEY = 'auth.token';

export function useSession() {
  const [token] = useMMKVString(TOKEN_KEY, storage);
  return { token };
}

export async function signIn(email: string, password: string) {
  const res = await fetch('/api/session', { method: 'POST', body: JSON.stringify({ email, password }) });
  const { token } = await res.json();
  storage.set(TOKEN_KEY, token);
}
