import { ScrollView, StyleSheet } from 'react-native';
import MapView from 'react-native-maps';
import { Text } from 'react-native-paper';

export function DetailsScreen() {
  return (
    <ScrollView contentContainerStyle={styles.body}>
      <Text variant="titleLarge">Heron at the weir</Text>
      <MapView style={styles.map} />
    </ScrollView>
  );
}

const styles = StyleSheet.create({ body: { padding: 16, gap: 12 }, map: { height: 240, borderRadius: 12 } });
