import { Link } from 'expo-router';
import { Pressable, StyleSheet, View } from 'react-native';

import { ThemedText } from '@/components/themed-text';
import { Spacing } from '@/constants/theme';
import { useTheme } from '@/hooks/use-theme';

export function OrderCard({ order }: { order: { id: string; title: string; total: string } }) {
  const colors = useTheme();
  return (
    <Link href={`/orders/${order.id}`} asChild>
      <Pressable style={[styles.card, { backgroundColor: colors.surface, borderColor: colors.border }]}>
        <View style={styles.row}>
          <ThemedText>{order.title}</ThemedText>
          <ThemedText type="muted" allowFontScaling={false}>{order.total}</ThemedText>
        </View>
      </Pressable>
    </Link>
  );
}

const styles = StyleSheet.create({
  card: { borderRadius: 12, borderWidth: 1, padding: Spacing.md },
  row: { flexDirection: 'row', justifyContent: 'space-between' },
});
