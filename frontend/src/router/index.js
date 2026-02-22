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
    meta: { requiresAuth: false, hideForAuth: true, title: 'Login' },
  },
  {
    path: '/register',
    name: 'Register',
    component: () => import('@/views/auth/RegisterView.vue'),
    meta: { requiresAuth: false, hideForAuth: true, title: 'Register' },
  },
  {
    path: '/library',
    name: 'Library',
    component: () => import('@/views/library/LibraryView.vue'),
    meta: { requiresAuth: true, title: 'Library' },
  },
  {
    path: '/library/shelf',
    name: 'HomeLibrary',
    component: () => import('@/views/library/PhysicalShelfView.vue'),
    meta: { requiresAuth: true, title: 'Home Library' },
  },
  {
    path: '/books',
    name: 'Books',
    component: () => import('@/views/books/BooksView.vue'),
    meta: { requiresAuth: true, title: 'Books' },
  },
  {
    path: '/books/:id',
    name: 'BookDetail',
    component: () => import('@/views/books/BookDetailView.vue'),
    meta: { requiresAuth: true, title: 'Book' },
  },
  {
    path: '/books/:id/study',
    name: 'BookStudy',
    component: () => import('@/views/study/StudyView.vue'),
    meta: { requiresAuth: true, title: 'Study Session' },
    props: (route) => {
      // Extract numeric ID from slug format (e.g., "14-ohridski-prolog" -> "14")
      const param = route.params.id
      const bookId = param && param.includes('-') ? param.split('-')[0] : param
      return {
        bookId,
        bookTitle: route.query.title || 'Study Session'
      }
    }
  },
  {
    path: '/books/:id/review',
    name: 'BookReview',
    component: () => import('@/views/books/BookReviewView.vue'),
    meta: { requiresAuth: true, title: 'Write Review' },
  },
  {
    path: '/books/:id/review-view',
    name: 'BookReviewRead',
    component: () => import('@/views/books/BookReviewReadView.vue'),
    meta: { requiresAuth: true, title: 'Review' },
  },
  {
    path: '/books/:id/review/:userId',
    name: 'UserReview',
    component: () => import('@/views/books/UserReviewView.vue'),
    meta: { requiresAuth: true, title: 'Review' },
  },
  {
    path: '/import',
    name: 'ImportBooks',
    component: () => import('@/views/import/ImportBooksView.vue'),
    meta: { requiresAuth: true, title: 'Import Books' },
  },
  {
    path: '/quotes',
    name: 'Quotes',
    component: () => import('@/views/quotes/QuotesView.vue'),
    meta: { requiresAuth: true, title: 'Quotes' },
  },
  {
    path: '/vocabulary',
    name: 'Vocabulary',
    component: () => import('@/views/vocabulary/VocabularyView.vue'),
    meta: { requiresAuth: true, title: 'Vocabulary' },
  },
  {
    path: '/lists',
    name: 'Lists',
    component: () => import('@/views/lists/ListsView.vue'),
    meta: { requiresAuth: true, title: 'Lists' },
  },
  {
    path: '/challenges',
    name: 'Challenges',
    component: () => import('@/views/challenges/ChallengesView.vue'),
    meta: { requiresAuth: true, title: 'Challenges' },
  },
  {
    path: '/reading-session/:id',
    name: 'ReadingSession',
    component: () => import('@/views/reading/ReadingSessionView.vue'),
    meta: { requiresAuth: true, title: 'Reading Session' },
  },
  {
    path: '/users/:id',
    name: 'UserProfile',
    component: () => import('@/views/social/UserProfileView.vue'),
    meta: { requiresAuth: true, title: 'Profile' },
  },
  {
    path: '/feed',
    name: 'Feed',
    component: () => import('@/views/feed/FeedView.vue'),
    meta: { requiresAuth: true, title: 'Feed' },
  },
  {
    path: '/correspondence',
    name: 'Correspondence',
    component: () => import('@/views/correspondence/CorrespondenceView.vue'),
    meta: { requiresAuth: true, title: 'Messages' },
  },
  {
    path: '/circles/:circleId?/:topicId?',
    name: 'Circles',
    component: () => import('@/views/social/CirclesView.vue'),
    meta: { requiresAuth: true, title: 'Circles' },
  },
  {
    path: '/friends',
    name: 'Friends',
    component: () => import('@/views/social/FriendsView.vue'),
    meta: { requiresAuth: true, title: 'Friends' },
  },
  {
    path: '/discover',
    name: 'Discover',
    component: () => import('@/views/recommendations/RecommendationsView.vue'),
    meta: { requiresAuth: true, title: 'Discover' },
  },
  {
    path: '/codex',
    name: 'Codex',
    component: () => import('@/views/codex/CodexView.vue'),
    meta: { requiresAuth: true, title: 'Codex' },
  },
  {
    path: '/manuscripts/shared/:token',
    name: 'SharedManuscript',
    component: () => import('@/views/codex/SharedManuscriptView.vue'),
    meta: { requiresAuth: false, title: 'Shared Manuscript' },
  },
  {
    path: '/authors/:id',
    name: 'AuthorDetail',
    component: () => import('@/views/authors/AuthorDetailView.vue'),
    meta: { requiresAuth: true, title: 'Author' },
  },
  {
    path: '/profile',
    name: 'Profile',
    component: () => import('@/views/profile/ProfileView.vue'),
    meta: { requiresAuth: true, title: 'Profile' },
  },
  {
    path: '/:pathMatch(.*)*',
    name: 'NotFound',
    component: () => import('@/views/NotFoundView.vue'),
    meta: { title: 'Not Found' },
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

// Update document title on navigation
router.afterEach((to) => {
  const title = to.meta.title
  document.title = title ? `${title} — Reading OS` : 'Reading OS'
})

export default router