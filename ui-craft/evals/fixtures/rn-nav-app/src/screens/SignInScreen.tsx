import { useState } from 'react';
import { StyleSheet, View } from 'react-native';
import { Button, Text, TextInput } from 'react-native-paper';

import { useSession } from '@/state/session';

export function SignInScreen() {
  const { signIn } = useSession();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  return (
    <View style={styles.form}>
      <Text variant="headlineMedium">Field notes</Text>
      <TextInput label="Email" value={email} onChangeText={setEmail} mode="outlined" />
      <TextInput label="Password" value={password} onChangeText={setPassword} secureTextEntry mode="outlined" />
      <Button mode="contained" onPress={() => signIn(email, password)}>Sign in</Button>
    </View>
  );
}

const styles = StyleSheet.create({ form: { flex: 1, justifyContent: 'center', padding: 24, gap: 12 } });
