import { createRouter, createWebHistory } from 'vue-router'
// import FBInstanceAuth from '../firebase/firebase_auth'
import Report from './views/Report.vue'
import Booking from './views/Booking.vue'


const routes = [
    // Example of a route. Add meta: { requiresAuth: true } to require authentication, else don't need to add.
    // {
    //     path: '/profile/:userId',
    //     name: 'ProfileView',
    //     component: ProfileView,
    //     meta: { requiresAuth: true }
    // }, 
    {
        path: '/report',
        name:'Report',
        component: Report
    },
    {
        path: '/booking',
        name:'Booking',
        component: Booking
    },

]


const router = createRouter({
    history: createWebHistory(),
    routes
})

// Optional: Navigation guard for authentication
// router.beforeEach((to, from, next) => {
//     const user = FBInstanceAuth.currentUser;
//     if (to.meta.requiresAuth && !user) {
//         next('/login'); // Redirect to login if not authenticated
//     } else {
//         next(); // Proceed as usual
//     }
// });

export default router;
