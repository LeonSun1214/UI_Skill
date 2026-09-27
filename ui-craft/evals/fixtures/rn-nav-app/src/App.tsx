import { NavigationContainer } from '@react-navigation/native';
import { useColorScheme } from 'react-native';
import { PaperProvider } from 'react-native-paper';

import { linking } from '@/navigation/linking';
import { RootNavigator } from '@/navigation/RootNavigator';
import { darkTheme, lightTheme } from '@/theme/paperTheme';

export default function App() {
  const scheme = useColorScheme();
  return (
    <PaperProvider theme={scheme === 'dark' ? darkTheme : lightTheme}>
      <NavigationContainer linking={linking}>
        <RootNavigator />
      </NavigationContainer>
    </PaperProvider>
  );
}
