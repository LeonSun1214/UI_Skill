import { FlatList, StyleSheet, View } from 'react-native';

import { OrderCard } from '@/components/order-card';
import { ThemedText } from '@/components/themed-text';
import { Spacing } from '@/constants/theme';
import { useOrdersQuery } from '@/lib/orders';

export default function OrdersScreen() {
  const { data } = useOrdersQuery();
  return (
    <View style={styles.container}>
      <ThemedText type="title">Today's orders</ThemedText>
      <FlatList
        data={data}
        keyExtractor={(o) => o.id}
        renderItem={({ item }) => <OrderCard order={item} />}
        contentContainerStyle={{ gap: Spacing.sm }}
      />
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, padding: Spacing.md, gap: Spacing.md },
});
