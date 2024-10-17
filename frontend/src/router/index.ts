import { createRouter, createWebHistory } from 'vue-router'
import HomeView from '../views/HomeView.vue'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/',
      name: 'home',
      component: HomeView,
    },
    {
      path: '/about',
      name: 'about',
      component: () => import('../views/AboutView.vue'),
    },
    {
      path: '/inspector/new',
      name: 'inspector-new',
      component: () => import('../views/NewInspectorView.vue'),
    },
    {
      path: '/inspector/:uuid',
      name: 'inspector-existing',
      component: () => import('../views/ExistingInspectorView.vue'),
    },
  ],
})

export default router
