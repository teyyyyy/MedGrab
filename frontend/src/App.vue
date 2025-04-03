<template>
  <div>
    <nav>
      <router-link to="/report">Reports</router-link>
      <router-link to="/booking">Bookings</router-link>
    </nav>
    <router-view />
  </div>
</template>


<!-- UPDATED "LOGIN PAGE" -->
<!-- <template>
  <div>
    <nav v-if="isAuthenticated">
      <router-link to="/report" v-if="isNurse">Reports</router-link>
      <router-link to="/booking" v-if="isPatient">Bookings</router-link>
      <button @click="logout">Logout</button>
    </nav>
    <router-view />
  </div>
</template>

<script>
import { computed } from 'vue'

export default {
  name: 'App',
  setup() {
    const isAuthenticated = computed(() => {
      return localStorage.getItem('userId') !== null
    })

    const isPatient = computed(() => {
      return localStorage.getItem('userRole') === 'patient'
    })

    const isNurse = computed(() => {
      return localStorage.getItem('userRole') === 'nurse'
    })

    const logout = () => {
      localStorage.removeItem('userRole')
      localStorage.removeItem('userId')
      window.location.href = '/'
    }

    return {
      isAuthenticated,
      isPatient,
      isNurse,
      logout
    }
  }
}
</script>

<style>
nav {
  padding: 1rem;
  background: #f5f5f5;
  display: flex;
  gap: 1rem;
}

nav a {
  text-decoration: none;
  color: #333;
  padding: 0.5rem 1rem;
  border-radius: 4px;
}

nav a.router-link-active {
  background: #ddd;
}

nav button {
  margin-left: auto;
  padding: 0.5rem 1rem;
  background: #f44336;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
}
</style> -->