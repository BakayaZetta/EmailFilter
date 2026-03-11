import { createRouter, createWebHistory } from 'vue-router'
import HomeView from '@/views/HomeView.vue'
import LoginView from '@/views/LoginView.vue'
import RegisterView from '@/views/RegisterView.vue'
import QuarantineView from '@/views/QuarantineView.vue'
import HistoryView from '@/views/HistoryView.vue'
import StatisticsView from '@/views/StatisticsView.vue'
import NotFoundView from '@/views/NotFoundView.vue'

const isAdminRole = (role) => {
  const normalizedRole = String(role || '').toLowerCase();
  return normalizedRole === 'admin' || normalizedRole === 'super_admin' || normalizedRole === 'superadmin';
};

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/',
      name: 'home',
      component: HomeView,
    },
    {
      path: '/login',
      name: 'login',
      component: LoginView,
    },
    {
      path: '/register',
      name: 'register',
      component: RegisterView,
    },
    {
      path: '/quarantine',
      name: 'quarantine',
      component: QuarantineView,
    },
    {
      path: '/history',
      name: 'history',
      component: HistoryView,
    },
    {
      path: '/statistics',
      name: 'statistics',
      component: StatisticsView,
    },
    {
      path: '/settings',
      name: 'settings',
      component: () => import('@/views/SettingsView.vue'),
      meta: { requiresAuth: true }
    },
    {
      path: '/admin',
      name: 'admin',
      component: () => import('@/views/AdminPortalView.vue'),
      meta: { requiresAuth: true, requiresAdmin: true }
    },
    {
      path: '/:pathMatch(.*)*',
      name: 'not-found',
      component: NotFoundView,
    },
    // {
    //   path: '/',
    //   name: 'home',
    //   component: HomeView,
    // },
    // {
    //   path: '/about',
    //   name: 'about',
    //   // route level code-splitting
    //   // this generates a separate chunk (About.[hash].js) for this route
    //   // which is lazy-loaded when the route is visited.
    //   component: () => import('../views/AboutView.vue'),
    // },
  ],
});

router.beforeEach((to, from, next) => {
  const token = sessionStorage.getItem('token');
  const userRaw = sessionStorage.getItem('user');
  const user = userRaw ? JSON.parse(userRaw) : null;

  if (to.meta.requiresAuth && !token) {
    return next('/login');
  }

  if (to.meta.requiresAdmin && !isAdminRole(user?.role)) {
    return next('/');
  }

  return next();
});

export default router
