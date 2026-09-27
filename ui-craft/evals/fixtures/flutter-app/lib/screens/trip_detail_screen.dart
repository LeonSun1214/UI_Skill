import 'package:flutter/material.dart';

import '../app/theme.dart';
import '../widgets/trip_card.dart';

class TripDetailScreen extends StatelessWidget {
  const TripDetailScreen({super.key, required this.id});

  final String id;

  @override
  Widget build(BuildContext context) {
    final trip = trips.firstWhere((t) => t.id == id, orElse: () => trips.first);
    final theme = Theme.of(context);
    return Scaffold(
      appBar: AppBar(title: Text(trip.name)),
      body: Padding(
        padding: const EdgeInsets.all(Insets.md),
        // A column that does not scroll: it fits a tall phone, and runs out of room on a small one.
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            SizedBox(height: 300, child: ColoredBox(color: theme.colorScheme.secondary)),
            const SizedBox(height: Insets.lg),
            Text(trip.region, style: theme.textTheme.headlineSmall),
            const SizedBox(height: Insets.sm),
            Text(
              '${trip.days} days, ${trip.km} km. Permits open in March, and the camps fill in the first hour: '
              'have a second itinerary ready.',
              style: theme.textTheme.bodyMedium,
            ),
            const SizedBox(height: Insets.sm),
            // The permit fee's tier: text with no letter or digit, in a grey below 4.5:1.
            Text(r'$$', style: theme.textTheme.bodySmall),
            const Spacer(),
            FilledButton(onPressed: () {}, child: const Text('Request a permit')),
          ],
        ),
      ),
    );
  }
}
