import 'package:flutter/material.dart';

class ProfileScreen extends StatelessWidget {
  const ProfileScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return ListView(
      children: const [
        ListTile(leading: Icon(Icons.person), title: Text('Sam Rivera'), subtitle: Text('sam@example.com')),
        ListTile(leading: Icon(Icons.notifications), title: Text('Notifications')),
        ListTile(leading: Icon(Icons.logout), title: Text('Sign out')),
      ],
    );
  }
}
