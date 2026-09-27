import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';

import '../app/theme.dart';

class Trip {
  const Trip(this.id, this.name, this.region, this.days, this.km);
  final String id, name, region;
  final int days, km;
}

const trips = [
  Trip('rainier', 'Wonderland Trail', 'Mt. Rainier', 3, 36),
  Trip('enchantments', 'The Enchantments', 'Alpine Lakes', 2, 29),
  Trip('olympic', 'High Divide Loop', 'Olympic', 2, 30),
];

class TripCard extends StatelessWidget {
  const TripCard({super.key, required this.trip});

  final Trip trip;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return Card(
      child: InkWell(
        onTap: () => context.go('/trips/${trip.id}'),
        child: Padding(
          padding: const EdgeInsets.all(Insets.md),
          child: Row(
            children: [
              Expanded(
                // A fixed height: the three lines fit at the default text size only.
                child: SizedBox(
                  height: 64,
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(trip.name, style: theme.textTheme.titleMedium),
                      Text(trip.region, style: theme.textTheme.bodySmall),
                      Text('${trip.days} days · ${trip.km} km',
                          style: theme.textTheme.bodyMedium?.copyWith(color: theme.colorScheme.outline)),
                    ],
                  ),
                ),
              ),
              // A 28px heart with no label: too small to tap, and silent to a screen reader.
              GestureDetector(
                onTap: () {},
                child: const SizedBox(width: 28, height: 28, child: Icon(Icons.favorite_border, size: 20)),
              ),
            ],
          ),
        ),
      ),
    );
  }
}
