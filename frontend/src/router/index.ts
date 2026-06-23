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
      component: () => import('@/views/backend/BackendLayout.vue'),
      children: [
        {
          path: '',
          redirect: '/backend/upload',
        },
        {
          path: 'upload',
          name: 'backend-upload',
          component: () => import('@/views/backend/BackendUpload.vue'),
        },
        {
          path: 'images',
          name: 'backend-images',
          component: () => import('@/views/backend/BackendImages.vue'),
        },
        {
          path: 'system',
          name: 'backend-system',
          component: () => import('@/views/backend/BackendSystem.vue'),
        },
      ],
    },
    {
      path: '/about',
      name: 'about',
      component: () => import('@/views/About.vue'),
    },
  ],
})

export default router
