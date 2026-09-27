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
      body: ListView(
        padding: const EdgeInsets.all(Insets.md),
        children: [
          Text(trip.region, style: theme.textTheme.headlineSmall),
          const SizedBox(height: Insets.sm),
          Text('${trip.days} days, ${trip.km} km. Permits open in March.', style: theme.textTheme.bodyMedium),
          const SizedBox(height: Insets.lg),
          FilledButton(onPressed: () {}, child: const Text('Request a permit')),
        ],
      ),
    );
  }
}
