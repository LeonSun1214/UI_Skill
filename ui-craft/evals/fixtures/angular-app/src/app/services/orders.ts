import { HttpClient } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { environment } from '../../environments/environment';

export interface Order {
  id: number;
  customer: string;
  total: number;
  status: 'paid' | 'pending' | 'refunded';
}

@Injectable({ providedIn: 'root' })
export class Orders {
  private http = inject(HttpClient);

  list() {
    return this.http.get<Order[]>(`${environment.apiUrl}/orders`);
  }

  stats() {
    return this.http.get<{ revenue: number; orders: number; refunds: number }>('/api/stats');
  }
}
