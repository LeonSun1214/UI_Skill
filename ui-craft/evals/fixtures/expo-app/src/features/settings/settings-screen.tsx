import { Platform, StyleSheet, Switch, View } from 'react-native';

import { ThemedText } from '@/components/themed-text';
import { Spacing } from '@/constants/theme';
import { useSchemeChoice } from '@/hooks/use-app-scheme';

export default function SettingsScreen() {
  const [choice, setChoice] = useSchemeChoice();
  return (
    <View style={styles.list}>
      <ThemedText type="title">Settings</ThemedText>
      <View style={styles.row}>
        <ThemedText>Dark mode</ThemedText>
        <Switch value={choice === 'dark'} onValueChange={(on) => setChoice(on ? 'dark' : 'light')} />
      </View>
      {Platform.OS === 'web' ? <ThemedText type="muted">Syncs with your browser</ThemedText> : null}
    </View>
  );
}

const styles = StyleSheet.create({
  list: { padding: Spacing.md, gap: Spacing.md },
  row: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center' },
});
