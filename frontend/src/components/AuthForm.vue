<template>
  <div>
    <h2>{{ isLogin ? 'Login' : 'Sign Up' }}</h2>
    <form @submit.prevent="handleAuth">
      <input v-model="email" type="email" placeholder="Email" required />
      <input v-model="password" type="password" placeholder="Password" required />
      <button type="submit">{{ isLogin ? 'Login' : 'Sign Up' }}</button>
    </form>
    <button @click="toggleForm">
      Switch to {{ isLogin ? 'Sign Up' : 'Login' }}
    </button>
  </div>
</template>

<script setup>
import { ref } from 'vue'

const email = ref('')
const password = ref('')
const isLogin = ref(true)

function toggleForm() {
  isLogin.value = !isLogin.value
}

async function handleAuth() {
  try {
    const endpoint = isLogin.value ? 'login' : 'signup'
    const res = await fetch(`http://localhost:5001/${endpoint}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        email: email.value,
        password: password.value
      })
    })

    const data = await res.json()
    if (!res.ok) throw new Error(data.error || 'Auth failed')

    alert(data.message)
  } catch (err) {
    alert(err.message)
  }
}
</script>

