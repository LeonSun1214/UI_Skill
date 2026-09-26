import { Injectable, inject } from '@angular/core';
import { CanActivate, Router, UrlTree } from '@angular/router';
import { AuthService } from '@app/auth/auth.service';

@Injectable({ providedIn: 'root' })
export class AdminGuard implements CanActivate {
  private auth = inject(AuthService);
  private router = inject(Router);

  canActivate(): boolean | UrlTree {
    return this.auth.isLoggedIn() ? true : this.router.parseUrl('/login');
  }
}
