import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';

/// The chrome around every signed-in page: a bottom bar on phones, a rail from 840 up.
class AppShell extends StatelessWidget {
  const AppShell({super.key, required this.location, required this.child});

  final String location;
  final Widget child;

  static const _paths = ['/trips', '/profile'];

  @override
  Widget build(BuildContext context) {
    final index = location.startsWith('/profile') ? 1 : 0;
    void go(int i) => context.go(_paths[i]);
    if (MediaQuery.sizeOf(context).width >= 840) {
      return Scaffold(
        body: Row(
          children: [
            NavigationRail(
              selectedIndex: index,
              onDestinationSelected: go,
              labelType: NavigationRailLabelType.all,
              destinations: const [
                NavigationRailDestination(icon: Icon(Icons.terrain), label: Text('Trips')),
                NavigationRailDestination(icon: Icon(Icons.person), label: Text('Profile')),
              ],
            ),
            const VerticalDivider(width: 1),
            Expanded(child: child),
          ],
        ),
      );
    }
    return Scaffold(
      body: child,
      bottomNavigationBar: NavigationBar(
        selectedIndex: index,
        onDestinationSelected: go,
        destinations: const [
          NavigationDestination(icon: Icon(Icons.terrain), label: 'Trips'),
          NavigationDestination(icon: Icon(Icons.person), label: 'Profile'),
        ],
      ),
    );
  }
}
