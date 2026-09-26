export default [
  {
    path: '/user',
    layout: false,
    routes: [{ path: '/user/login', name: 'login', component: './user/login' }],
  },
  { path: '/welcome', name: 'welcome', component: './Welcome' },
  {
    path: '/admin',
    name: 'admin',
    access: 'canAdmin',
    routes: [{ path: '/admin/users', name: 'users', component: './admin/users' }],
  },
  { path: '/list', name: 'list', component: './table-list' },
  { path: '/', redirect: '/welcome' },
  { path: '*', layout: false, component: './404' },
];
