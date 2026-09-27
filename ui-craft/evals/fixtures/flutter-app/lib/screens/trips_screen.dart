import 'package:flutter/material.dart';

import '../app/theme.dart';
import '../widgets/trip_card.dart';

class TripsScreen extends StatelessWidget {
  const TripsScreen({super.key});

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return SafeArea(
      child: ListView(
        padding: const EdgeInsets.all(Insets.md),
        children: [
          // The title and the filters in one row: it fits a tablet, not a phone.
          Row(
            children: [
              Text('Upcoming trips', style: theme.textTheme.headlineSmall),
              const SizedBox(width: Insets.md),
              FilterChip(label: const Text('This month'), selected: true, onSelected: (_) {}),
              const SizedBox(width: Insets.sm),
              FilterChip(label: const Text('Overnight'), selected: false, onSelected: (_) {}),
              // An icon button without a tooltip has no label.
              IconButton(onPressed: () {}, icon: const Icon(Icons.tune)),
            ],
          ),
          const SizedBox(height: Insets.md),
          for (final trip in trips) TripCard(trip: trip),
        ],
      ),
    );
  }
}
