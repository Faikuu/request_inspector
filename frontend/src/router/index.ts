import { createRouter, createWebHistory, type RouteRecordRaw } from 'vue-router'
import HomeView from '@/views/HomeView.vue'

declare module 'vue-router' {
  interface RouteMeta {
    title?: string
  }
}

const APP = 'Request Inspector'

const routes: RouteRecordRaw[] = [
  { path: '/', name: 'home', component: HomeView, meta: { title: APP } },
  {
    path: '/new',
    name: 'new',
    component: () => import('@/views/CreateInboxView.vue'),
    meta: { title: `Create an inbox — ${APP}` },
  },
  {
    path: '/open',
    name: 'open',
    component: () => import('@/views/OpenInboxView.vue'),
    meta: { title: `Open an inbox — ${APP}` },
  },
  {
    path: '/i/:id',
    name: 'inbox',
    component: () => import('@/views/InboxView.vue'),
    meta: { title: `Inbox — ${APP}` },
  },
  // Legacy URLs
  { path: '/inspector/new', redirect: '/new' },
  { path: '/inspector', redirect: '/open' },
  { path: '/inspector/:uuid', redirect: (to) => `/i/${String(to.params.uuid)}` },
  {
    path: '/:pathMatch(.*)*',
    name: 'not-found',
    component: () => import('@/views/NotFoundView.vue'),
    meta: { title: `Page not found — ${APP}` },
  },
]

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes,
  scrollBehavior: () => ({ top: 0 }),
})

router.afterEach((to) => {
  document.title = to.meta.title ?? APP
})

export default router
