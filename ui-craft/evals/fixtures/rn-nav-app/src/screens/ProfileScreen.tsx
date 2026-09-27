import { StyleSheet, View } from 'react-native';
import { Avatar, List, Switch, Text } from 'react-native-paper';

import { colors } from '@/theme/colors';

export function ProfileScreen() {
  return (
    <View style={styles.page}>
      <Avatar.Text label="RM" />
      <Text variant="titleLarge">Rosa Marsh</Text>
      <List.Item title="Offline maps" right={() => <Switch value />} />
      <Text style={styles.caption} allowFontScaling={false}>Synced 2 minutes ago</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  page: { flex: 1, padding: 16, gap: 12 },
  caption: { color: colors.textDim, fontSize: 12 },
});
