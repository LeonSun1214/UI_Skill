import { Component } from '@angular/core';
import { MatCardModule } from '@angular/material/card';

@Component({
  selector: 'app-profile',
  imports: [MatCardModule],
  template: `
    <mat-card appearance="outlined">
      <mat-card-header><mat-card-title>Profile</mat-card-title></mat-card-header>
      <mat-card-content><p class="muted">Your name and avatar appear on every order you create.</p></mat-card-content>
    </mat-card>
  `,
  styles: `.muted { color: var(--mat-sys-on-surface-variant); }`,
})
export class Profile {}
