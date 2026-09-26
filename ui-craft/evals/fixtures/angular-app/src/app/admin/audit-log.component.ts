import { Component, Input } from '@angular/core';

@Component({
  selector: 'app-audit-log',
  standalone: false,
  template: `
    <table mat-table [dataSource]="rows">
      <ng-container matColumnDef="who">
        <th mat-header-cell *matHeaderCellDef>Who</th>
        <td mat-cell *matCellDef="let r">{{ r.who }}</td>
      </ng-container>
      <tr mat-header-row *matHeaderRowDef="['who']"></tr>
      <tr mat-row *matRowDef="let row; columns: ['who']"></tr>
    </table>
  `,
})
export class AuditLogComponent {
  @Input() limit = 50;
  rows = [{ who: 'ada' }, { who: 'grace' }];
}
