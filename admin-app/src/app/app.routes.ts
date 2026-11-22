import type { Routes } from '@angular/router';

export const routes: Routes = [
  {
    path: 'home',
    loadComponent: () => import('./home/home.page').then((m) => m.HomePage),
  },
  {
    path: '',
    redirectTo: 'home',
    pathMatch: 'full',
  },
  {
    path: 'login',
    loadComponent: () => import('./pages/login/login.page').then((m) => m.LoginPage),
  },
  {
    path: 'home',
    loadComponent: () => import('./pages/home/home.page').then((m) => m.HomePage),
  },
  {
    path: 'profile',
    loadComponent: () => import('./pages/profile/profile.page').then((m) => m.ProfilePage),
  },
  {
    path: 'complaints',
    loadComponent: () => import('./pages/complaints/complaints.page').then((m) => m.ComplaintsPage),
  },
  {
    path: 'cfa-view',
    loadComponent: () => import('./pages/cfa-view/cfa-view.page').then((m) => m.CfaViewPage),
  },
  {
    path: 'audit-logs',
    loadComponent: () => import('./pages/audit-logs/audit-logs.page').then((m) => m.AuditLogsPage),
  },
];
