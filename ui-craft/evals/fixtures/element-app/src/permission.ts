import router from './router';
import { getRouters } from '@/api/menu';

router.beforeEach(async (to) => {
  if (to.path === '/login') return true;
  const menus = await getRouters();
  for (const m of menus) router.addRoute({ path: m.path, component: () => import(`@/views/${m.component}.vue`) });
  return true;
});
