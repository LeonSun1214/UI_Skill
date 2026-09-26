import { Component, inject } from '@angular/core';
import { BreakpointObserver, Breakpoints } from '@angular/cdk/layout';
import { AsyncPipe } from '@angular/common';
import { Router, RouterLink, RouterLinkActive, RouterOutlet } from '@angular/router';
import { MatToolbarModule } from '@angular/material/toolbar';
import { MatButtonModule } from '@angular/material/button';
import { MatSidenavModule } from '@angular/material/sidenav';
import { MatListModule } from '@angular/material/list';
import { MatIconModule } from '@angular/material/icon';
import { Observable } from 'rxjs';
import { map, shareReplay } from 'rxjs/operators';
import { AuthService } from '../auth/auth.service';
import { ThemeService } from '../theme.service';

@Component({
  selector: 'app-shell',
  templateUrl: './shell.component.html',
  styleUrl: './shell.component.scss',
  imports: [
    MatToolbarModule,
    MatButtonModule,
    MatSidenavModule,
    MatListModule,
    MatIconModule,
    AsyncPipe,
    RouterLink,
    RouterLinkActive,
    RouterOutlet,
  ],
})
export class ShellComponent {
  private breakpointObserver = inject(BreakpointObserver);
  private auth = inject(AuthService);
  private router = inject(Router);
  protected theme = inject(ThemeService);

  links = [
    { path: '/dashboard', label: 'Dashboard', icon: 'space_dashboard' },
    { path: '/orders', label: 'Orders', icon: 'receipt_long' },
    { path: '/settings', label: 'Settings', icon: 'settings' },
  ];

  isHandset$: Observable<boolean> = this.breakpointObserver.observe(Breakpoints.Handset).pipe(
    map((result) => result.matches),
    shareReplay(),
  );

  logout() {
    this.auth.logout();
    this.router.navigate(['/login']);
  }
}
