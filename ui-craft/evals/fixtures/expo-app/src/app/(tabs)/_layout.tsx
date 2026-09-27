import { Redirect, Tabs } from 'expo-router';

import { useSession } from '@/lib/session';

export default function TabsLayout() {
  const { token } = useSession();

  if (!token) {
    return <Redirect href="/sign-in" />;
  }
  return (
    <Tabs>
      <Tabs.Screen name="index" options={{ title: 'Orders' }} />
      <Tabs.Screen name="settings" options={{ title: 'Settings' }} />
    </Tabs>
  );
}
