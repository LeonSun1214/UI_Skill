import { FlatList, StyleSheet } from 'react-native';
import { Card, FAB, Text } from 'react-native-paper';

import { spacing } from '@/theme/spacing';

export function FeedScreen() {
  const notes = [{ id: '1', title: 'Heron at the weir', body: 'Two sightings before seven.' }];
  return (
    <>
      <FlatList
        data={notes}
        contentContainerStyle={styles.list}
        renderItem={({ item }) => (
          <Card mode="outlined">
            <Card.Title title={item.title} />
            <Card.Content><Text variant="bodyMedium">{item.body}</Text></Card.Content>
          </Card>
        )}
      />
      <FAB icon="plus" style={styles.fab} accessibilityLabel="New note" />
    </>
  );
}

const styles = StyleSheet.create({
  list: { padding: spacing.md, gap: spacing.sm },
  fab: { position: 'absolute', right: spacing.lg, bottom: spacing.lg },
});
