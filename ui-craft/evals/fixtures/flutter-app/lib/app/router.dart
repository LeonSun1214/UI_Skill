import 'package:go_router/go_router.dart';

import '../screens/profile_screen.dart';
import '../screens/sign_in_screen.dart';
import '../screens/trip_detail_screen.dart';
import '../screens/trips_screen.dart';
import '../widgets/app_shell.dart';
import 'auth.dart';

final router = GoRouter(
  initialLocation: '/trips',
  refreshListenable: auth,
  redirect: (context, state) {
    final atSignIn = state.matchedLocation == '/sign-in';
    if (!auth.signedIn && !atSignIn) return '/sign-in';
    if (auth.signedIn && atSignIn) return '/trips';
    return null;
  },
  routes: [
    GoRoute(path: '/sign-in', builder: (context, state) => const SignInScreen()),
    ShellRoute(
      builder: (context, state, child) => AppShell(location: state.matchedLocation, child: child),
      routes: [
        GoRoute(
          path: '/trips',
          builder: (context, state) => const TripsScreen(),
          routes: [
            GoRoute(
              path: ':id',
              builder: (context, state) => TripDetailScreen(id: state.pathParameters['id']!),
            ),
          ],
        ),
        GoRoute(path: '/profile', builder: (context, state) => const ProfileScreen()),
      ],
    ),
  ],
);
