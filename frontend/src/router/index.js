import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '../stores/auth'

const routes = [
  {
    path: '/',
    name: 'Home',
    component: () => import('../views/Home.vue'),
  },
  {
    path: '/portfolio',
    name: 'Portfolio',
    component: () => import('../views/Portfolio.vue'),
  },
  {
    path: '/portfolio/:slug',
    name: 'ProjectDetail',
    component: () => import('../views/ProjectDetail.vue'),
  },
  {
    path: '/login',
    name: 'Login',
    component: () => import('../views/Login.vue'),
  },
  {
    path: '/register',
    name: 'Register',
    component: () => import('../views/Register.vue'),
  },
  {
    path: '/devis',
    name: 'Devis',
    component: () => import('../views/Devis.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/mes-devis',
    name: 'MesDevis',
    component: () => import('../views/MesDevis.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/devis/:id',
    name: 'DevisDetail',
    component: () => import('../views/DevisDetail.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/signature/:token',
    name: 'SignatureDevis',
    component: () => import('../views/SignatureDevis.vue'),
    meta: { requiresAuth: false }
  },
  {
    path: '/admin/devis',
    name: 'AdminDevis',
    component: () => import('../views/AdminDevis.vue'),
    meta: { requiresAuth: true, requiresAdmin: true }
  },
  {
    path: '/contact',
    name: 'Contact',
    component: () => import('../views/Contact.vue'),
  },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
  scrollBehavior(to, from, savedPosition) {
    if (savedPosition) {
      return savedPosition
    } else if (to.hash) {
      return {
        el: to.hash,
        behavior: 'smooth',
      }
    } else {
      return { top: 0, behavior: 'smooth' }
    }
  },
})

// Guard pour protéger les routes
router.beforeEach((to, from, next) => {
  const authStore = useAuthStore()

  if (to.meta.requiresAuth) {
    const token = localStorage.getItem('accessToken')
    if (!token) {
      next('/login')
    } else if (to.meta.requiresAdmin && !authStore.user?.is_staff) {
      // Rediriger si l'utilisateur n'est pas admin
      next('/')
    } else {
      next()
    }
  } else {
    next()
  }
})

// SEO Guard
import { useSEO } from '../composables/useSEO'

router.afterEach((to) => {
  const defaultTitle = 'Solutions Web & Mobile'
  const defaultDesc = 'Zsdevweb - Solutions web innovantes, développement sur mesure, applications mobiles et design UI/UX.'

  let title = defaultTitle
  let description = defaultDesc

  switch (to.name) {
    case 'Home':
      title = 'Accueil'
      break
    case 'Portfolio':
      title = 'Portfolio'
      description = 'Découvrez nos réalisations : sites web, applications mobiles et designs uniques.'
      break
    case 'Devis':
      title = 'Demander un Devis'
      description = 'Obtenez une estimation gratuite pour votre projet web ou mobile en quelques clics.'
      break
    case 'Contact':
      title = 'Contact'
      description = 'Contactez-nous pour discuter de votre projet digital.'
      break
    case 'Login':
      title = 'Connexion'
      break
    case 'Register':
      title = 'Inscription'
      break
  }

  useSEO(title, description)
})

export default router