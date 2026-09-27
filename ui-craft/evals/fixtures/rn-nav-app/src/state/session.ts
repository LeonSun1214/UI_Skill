import AsyncStorage from '@react-native-async-storage/async-storage';
import { useEffect, useState } from 'react';

const SESSION_KEY = 'session.token';

export function useSession() {
  const [token, setToken] = useState<string | null>(null);
  useEffect(() => {
    AsyncStorage.getItem(SESSION_KEY).then(setToken);
  }, []);
  const signIn = async (email: string, password: string) => {
    const t = `${email}:${password.length}`;
    await AsyncStorage.setItem(SESSION_KEY, t);
    setToken(t);
  };
  return { signedIn: !!token, signIn };
}
