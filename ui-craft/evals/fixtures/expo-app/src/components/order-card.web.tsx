import { Link } from 'expo-router';
import { StyleSheet, View } from 'react-native';

import { ThemedText } from '@/components/themed-text';
import { Spacing } from '@/constants/theme';
import { useTheme } from '@/hooks/use-theme';

// On the web a card is a plain link: no Pressable feedback, a hover underline instead.
export function OrderCard({ order }: { order: { id: string; title: string; total: string } }) {
  const colors = useTheme();
  return (
    <Link href={`/orders/${order.id}`} style={[styles.card, { borderColor: colors.border }]}>
      <View style={styles.row}>
        <ThemedText>{order.title}</ThemedText>
        <ThemedText type="muted">{order.total}</ThemedText>
      </View>
    </Link>
  );
}

const styles = StyleSheet.create({
  card: { borderRadius: 12, borderWidth: 1, padding: Spacing.md },
  row: { flexDirection: 'row', justifyContent: 'space-between' },
});
