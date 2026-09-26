import Dashboard from 'views/admin/default';
import Orders from 'views/admin/orders';
import SignIn from 'views/auth/signIn';

const routes = [
  { name: 'Dashboard', layout: '/admin', path: '/default', component: <Dashboard /> },
  { name: 'Orders', layout: '/admin', path: '/orders', component: <Orders /> },
  { name: 'Sign in', layout: '/auth', path: '/sign-in', component: <SignIn /> },
];

export default routes;
