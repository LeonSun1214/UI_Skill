import { Component, computed, input, output } from '@angular/core';
import { DecimalPipe } from '@angular/common';
import { MatCardModule } from '@angular/material/card';
import { MatIconModule } from '@angular/material/icon';

@Component({
  selector: 'app-stat-card',
  imports: [MatCardModule, MatIconModule, DecimalPipe],
  templateUrl: './stat-card.html',
  styleUrl: './stat-card.scss',
})
export class StatCard {
  label = input.required<string>();
  value = input(0);
  unit = input<string>('');
  trend = input<'up' | 'down' | null>(null);
  selected = output<string>();

  trendIcon = computed(() => (this.trend() === 'down' ? 'trending_down' : 'trending_up'));
}
