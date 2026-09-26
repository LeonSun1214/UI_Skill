import { Injectable, signal } from '@angular/core';

const TOKEN_KEY = 'ng-demo-token';

@Injectable({ providedIn: 'root' })
export class AuthService {
  readonly token = signal<string | null>(localStorage.getItem(TOKEN_KEY));

  isLoggedIn(): boolean {
    return this.token() !== null;
  }

  login(token: string) {
    localStorage.setItem(TOKEN_KEY, token);
    this.token.set(token);
  }

  logout() {
    localStorage.removeItem(TOKEN_KEY);
    this.token.set(null);
  }
}
