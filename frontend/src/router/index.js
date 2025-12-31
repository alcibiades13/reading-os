import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '@/stores/authStore'

const routes = [
  {
    path: '/',
    redirect: '/library',
  },
  {
    path: '/home',
    redirect: '/library',
  },
  {
    path: '/login',
    name: 'Login',
    component: () => import('@/views/auth/LoginView.vue'),
    meta: { requiresAuth: false, hideForAuth: true },
  },
  {
    path: '/register',
    name: 'Register',
    component: () => import('@/views/auth/RegisterView.vue'),
    meta: { requiresAuth: false, hideForAuth: true },
  },
  {
    path: '/library',
    name: 'Library',
    component: () => import('@/views/library/LibraryView.vue'),
    meta: { requiresAuth: true },
  },
  {
    path: '/books',
    name: 'Books',
    component: () => import('@/views/books/BooksView.vue'),
    meta: { requiresAuth: true },
  },
  {
    path: '/books/:id',
    name: 'BookDetail',
    component: () => import('@/views/books/BookDetailView.vue'),
    meta: { requiresAuth: true },
  },
  {
    path: '/books/:id/review',
    name: 'BookReview',
    component: () => import('@/views/books/BookReviewView.vue'),
    meta: { requiresAuth: true },
  },
  {
    path: '/books/:id/review-view',
    name: 'BookReviewRead',
    component: () => import('@/views/books/BookReviewReadView.vue'),
    meta: { requiresAuth: true },
  },
  {
    path: '/import',
    name: 'ImportBooks',
    component: () => import('@/views/import/ImportBooksView.vue'),
    meta: { requiresAuth: true },
  },
  {
    path: '/quotes',
    name: 'Quotes',
    component: () => import('@/views/quotes/QuotesView.vue'),
    meta: { requiresAuth: true },
  },
  {
    path: '/vocabulary',
    name: 'Vocabulary',
    component: () => import('@/views/vocabulary/VocabularyView.vue'),
    meta: { requiresAuth: true },
  },
  {
    path: '/lists',
    name: 'Lists',
    component: () => import('@/views/lists/ListsView.vue'),
    meta: { requiresAuth: true },
  },
  {
    path: '/challenges',
    name: 'Challenges',
    component: () => import('@/views/challenges/ChallengesView.vue'),
    meta: { requiresAuth: true },
  },
  {
    path: '/reading-session/:id',
    name: 'ReadingSession',
    component: () => import('@/views/reading/ReadingSessionView.vue'),
    meta: { requiresAuth: true },
  },
    {
    path: '/users/:id',
    name: 'UserProfile',
    component: () => import('@/views/social/UserProfileView.vue'),
    meta: { requiresAuth: true },
  },
  {
    path: '/feed',
    name: 'Feed',
    component: () => import('@/views/feed/FeedView.vue'),
    meta: { requiresAuth: true },
  },
  {
    path: '/circles',
    name: 'Circles',
    component: () => import('@/views/social/CirclesView.vue'),
    meta: { requiresAuth: true },
  },
  {
    path: '/profile',
    name: 'Profile',
    component: () => import('@/views/profile/ProfileView.vue'),
    meta: { requiresAuth: true },
  },
  {
    path: '/:pathMatch(.*)*',
    name: 'NotFound',
    component: () => import('@/views/NotFoundView.vue'),
  },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
  scrollBehavior(to, from, savedPosition) {
    if (savedPosition) {
      return savedPosition
    } else {
      return { top: 0 }
    }
  },
})

// Navigation guard - protect routes
router.beforeEach((to, from, next) => {
  const authStore = useAuthStore()
  
  // Initialize auth state if not already done
  if (!authStore.isAuthenticated) {
    authStore.initAuth()
  }

  const requiresAuth = to.matched.some((record) => record.meta.requiresAuth)
  const hideForAuth = to.matched.some((record) => record.meta.hideForAuth)

  if (requiresAuth && !authStore.isAuthenticated) {
    // Redirect to login if trying to access protected route
    next({ name: 'Login', query: { redirect: to.fullPath } })
  } else if (hideForAuth && authStore.isAuthenticated) {
    // Redirect authenticated users away from login/register
    next({ name: 'Library' })
  } else {
    next()
  }
})

export default router