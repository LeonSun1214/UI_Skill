import { NgModule } from '@angular/core';
import { CommonModule } from '@angular/common';
import { MatCardModule } from '@angular/material/card';
import { MatTableModule } from '@angular/material/table';
import { AdminRoutingModule } from './admin-routing.module';
import { AdminHomeComponent } from './admin-home.component';
import { AuditLogComponent } from './audit-log.component';

@NgModule({
  declarations: [AdminHomeComponent, AuditLogComponent],
  imports: [CommonModule, MatCardModule, MatTableModule, AdminRoutingModule],
})
export class AdminModule {}
