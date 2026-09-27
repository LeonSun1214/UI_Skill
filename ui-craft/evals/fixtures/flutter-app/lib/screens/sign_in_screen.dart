import 'package:flutter/material.dart';

import '../app/auth.dart';
import '../app/theme.dart';

class SignInScreen extends StatelessWidget {
  const SignInScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: Center(
        child: ConstrainedBox(
          constraints: const BoxConstraints(maxWidth: 400),
          child: Padding(
            padding: const EdgeInsets.all(Insets.lg),
            child: Column(
              mainAxisSize: MainAxisSize.min,
              crossAxisAlignment: CrossAxisAlignment.stretch,
              children: [
                Text('Sign in to Trailhead', style: Theme.of(context).textTheme.headlineSmall),
                const SizedBox(height: Insets.lg),
                const TextField(decoration: InputDecoration(labelText: 'Email')),
                const SizedBox(height: Insets.md),
                const TextField(obscureText: true, decoration: InputDecoration(labelText: 'Password')),
                const SizedBox(height: Insets.lg),
                FilledButton(onPressed: auth.signIn, child: const Text('Sign in')),
              ],
            ),
          ),
        ),
      ),
    );
  }
}
