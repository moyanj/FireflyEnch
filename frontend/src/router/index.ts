import { createRouter, createWebHistory } from 'vue-router'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: '/',
      name: 'home',
      component: () => import('@/views/Home.vue'),
    },
    {
      path: '/search',
      name: 'search',
      component: () => import('@/views/Search.vue'),
    },
    {
      path: '/image/:id',
      name: 'image-detail',
      component: () => import('@/views/ImageDetail.vue'),
    },
    {
      path: '/backend',
      name: 'backend',
      component: () => import('@/views/Backend.vue'),
    },
    {
      path: '/about',
      name: 'about',
      component: () => import('@/views/About.vue'),
    },
  ],
})

export default router
