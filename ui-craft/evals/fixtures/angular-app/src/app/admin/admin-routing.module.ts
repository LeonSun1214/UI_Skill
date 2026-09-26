import { NgModule } from '@angular/core';
import { RouterModule, Routes } from '@angular/router';
import { AdminHomeComponent } from './admin-home.component';
import { AuditLogComponent } from './audit-log.component';
import { AdminGuard } from './admin.guard';

const routes: Routes = [
  { path: '', component: AdminHomeComponent, title: 'Admin' },
  { path: 'audit', component: AuditLogComponent, canActivate: [AdminGuard], title: 'Audit log' },
];

@NgModule({
  imports: [RouterModule.forChild(routes)],
  exports: [RouterModule],
})
export class AdminRoutingModule {}
