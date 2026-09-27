import { createNativeStackNavigator } from '@react-navigation/native-stack';

import { useSession } from '@/state/session';
import { DetailsScreen } from '@/screens/DetailsScreen';
import { SignInScreen } from '@/screens/SignInScreen';

import { MainTabs } from './MainTabs';

const Stack = createNativeStackNavigator();

export function RootNavigator() {
  const { signedIn } = useSession();
  return (
    <Stack.Navigator initialRouteName={signedIn ? 'Main' : 'SignIn'}>
      {signedIn ? (
        <>
          <Stack.Screen name="Main" component={MainTabs} options={{ headerShown: false }} />
          <Stack.Screen name="Details" component={DetailsScreen} />
        </>
      ) : (
        <Stack.Screen name="SignIn" component={SignInScreen} options={{ title: 'Sign in' }} />
      )}
    </Stack.Navigator>
  );
}
