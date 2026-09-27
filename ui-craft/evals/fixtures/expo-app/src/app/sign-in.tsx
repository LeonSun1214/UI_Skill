import { useState } from 'react';
import { Pressable, StyleSheet, TextInput, View } from 'react-native';

import { ThemedText } from '@/components/themed-text';
import { Colors, Spacing } from '@/constants/theme';
import { signIn } from '@/lib/session';

export default function SignInScreen() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  return (
    <View style={styles.form}>
      <ThemedText type="title">Welcome back</ThemedText>
      <TextInput value={email} onChangeText={setEmail} placeholder="Email" style={styles.input} />
      <TextInput value={password} onChangeText={setPassword} placeholder="Password" secureTextEntry style={styles.input} />
      <Pressable onPress={() => signIn(email, password)} style={styles.button} hitSlop={8}>
        <ThemedText style={{ color: '#ffffff' }}>Sign in</ThemedText>
      </Pressable>
    </View>
  );
}

const styles = StyleSheet.create({
  form: { flex: 1, justifyContent: 'center', padding: Spacing.lg, gap: Spacing.sm },
  input: { borderWidth: 1, borderColor: Colors.light.border, borderRadius: 8, padding: 12, fontSize: 16 },
  button: { backgroundColor: Colors.light.tint, borderRadius: 8, padding: 14, alignItems: 'center' },
});
