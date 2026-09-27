import { Link } from 'expo-router';

import { ThemedText } from '@/components/themed-text';

export default function NotFound() {
  return (
    <Link href="/">
      <ThemedText>Back to orders</ThemedText>
    </Link>
  );
}
