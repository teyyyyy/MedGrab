// import { createRouter, createWebHistory } from 'vue-router'
// import Report from './views/Report.vue'
// import Booking from './views/Booking.vue'


// const routes = [
//     {
//         path: '/report',
//         name:'Report',
//         component: Report
//     },
//     {
//         path: '/booking',
//         name:'Booking',
//         component: Booking
//     },

// ]


// const router = createRouter({
//     history: createWebHistory(),
//     routes
// })

// THIS IS TO REDIRECT PATIENT/NURSE TO THEIR RESPECTIVE PAGES!!!!!

import { createRouter, createWebHistory } from 'vue-router'
import Report from './views/Report.vue'
import BookingCreator from './views/BookingCreator.vue'
import Login from './views/Login.vue'
import BookingManager from "./views/BookingManager.vue";

const routes = [
  {
    path: '/',
    name: 'Login',
    component: Login
  },
  {
    path: '/report',
    name: 'Report',
    component: Report,
    meta: { requiresAuth: true, requiresNurse: true }
  },
  {
    path: '/bookingcreator',
    name: 'Booking Creator',
    component: BookingCreator,
    meta: { requiresAuth: true, requiresPatient: true }
  },
  {
    path: '/bookingmanager',
    name: 'Booking Manager',
    component: BookingManager,
    meta: { requiresAuth: true, requiresNurse: true }
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

// Add navigation guard
router.beforeEach((to, from, next) => {
  const isAuthenticated = localStorage.getItem('userId') !== null
  const userRole = localStorage.getItem('userRole')
  
  if (to.matched.some(record => record.meta.requiresAuth)) {
    if (!isAuthenticated) {
      next('/')
    } else if (to.meta.requiresNurse && userRole !== 'nurse') {
      next('/booking') // or show error
    } else if (to.meta.requiresPatient && userRole !== 'patient') {
      next('/report') // or show error
    } else {
      next()
    }
  } else {
    next()
  }
})

export default router
