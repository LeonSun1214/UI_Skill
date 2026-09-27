import { StyleSheet, Text, type TextProps } from 'react-native';

import { useTheme } from '@/hooks/use-theme';

type Props = TextProps & { type?: 'default' | 'title' | 'muted' };

export function ThemedText({ style, type = 'default', ...rest }: Props) {
  const colors = useTheme();
  return <Text style={[{ color: type === 'muted' ? colors.textMuted : colors.text }, styles[type], style]} {...rest} />;
}

const styles = StyleSheet.create({
  default: { fontSize: 16, lineHeight: 24, fontFamily: 'Inter_400Regular' },
  title: { fontSize: 28, lineHeight: 34, fontFamily: 'Inter_600SemiBold' },
  muted: { fontSize: 14, lineHeight: 20, fontFamily: 'Inter_400Regular' },
});
