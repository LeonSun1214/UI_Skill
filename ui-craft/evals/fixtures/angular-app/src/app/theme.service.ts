import { Injectable, signal } from '@angular/core';

const KEY = 'ng-demo-theme';

@Injectable({ providedIn: 'root' })
export class ThemeService {
  readonly dark = signal(localStorage.getItem(KEY) === 'dark');

  constructor() {
    this.apply();
  }

  toggle() {
    this.dark.update((d) => !d);
    localStorage.setItem(KEY, this.dark() ? 'dark' : 'light');
    this.apply();
  }

  private apply() {
    document.documentElement.classList.toggle('dark-theme', this.dark());
  }
}
