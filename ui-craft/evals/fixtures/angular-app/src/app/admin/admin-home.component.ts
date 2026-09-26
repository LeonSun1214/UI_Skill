import { Component } from '@angular/core';

@Component({
  selector: 'app-admin-home',
  standalone: false,
  templateUrl: './admin-home.component.html',
})
export class AdminHomeComponent {
  sections = ['Users', 'Billing', 'Audit log'];
}
