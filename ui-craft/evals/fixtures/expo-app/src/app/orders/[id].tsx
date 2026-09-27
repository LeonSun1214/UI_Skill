import { useLocalSearchParams } from 'expo-router';
import { ScrollView, StyleSheet } from 'react-native';

import { ThemedText } from '@/components/themed-text';
import { Spacing } from '@/constants/theme';

export default function OrderScreen() {
  const { id } = useLocalSearchParams<{ id: string }>();
  return (
    <ScrollView contentContainerStyle={styles.body}>
      <ThemedText type="title">Order {id}</ThemedText>
      <ThemedText type="muted">Placed this morning</ThemedText>
    </ScrollView>
  );
}

const styles = StyleSheet.create({ body: { padding: Spacing.md, gap: Spacing.sm } });
