import { Component, inject } from '@angular/core';
import { toSignal } from '@angular/core/rxjs-interop';
import { Orders } from '../services/orders';
import { StatCard } from '../components/stat-card/stat-card';

@Component({
  selector: 'app-reports-page',
  imports: [StatCard],
  template: `
    <h1>Reports</h1>
    @for (o of orders() ?? []; track o.id) {
      <app-stat-card [label]="o.customer" [value]="o.total" unit="$" />
    }
  `,
})
export class ReportsPage {
  protected orders = toSignal(inject(Orders).list());
}
