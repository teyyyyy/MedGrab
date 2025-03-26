<template>
  <div>
    <h1>Welcome to MedGrab</h1>
    <img src="/MedGrab_logo.png" alt="MedGrab Logo" style="max-width: 200px; margin-bottom: 20px;" />

    <h2>{{ isLogin ? 'Login' : 'Sign Up' }}</h2>

    <form @submit.prevent="handleAuth">
      <div v-if="!isLogin">
        <input v-model="name" type="text" placeholder="Name" required />
        <br />
        <input v-model="phone" type="tel" placeholder="Phone Number" required />
        <br />
        <input v-model="medicalRecord" type="text" placeholder="Medical Record" required />
        <br />
        <input v-model="location" type="text" placeholder="Location" required />
        <br />
      </div>

      <input v-model="email" type="email" placeholder="Email" required />
      <br />
      <input v-model="password" type="password" placeholder="Password" required />
      <br />

      <button type="submit">{{ isLogin ? 'Login' : 'Sign Up' }}</button>
    </form>

    <button @click="toggleForm">
      Switch to {{ isLogin ? 'Sign Up' : 'Login' }}
    </button>
  </div>
</template>



<script setup>
import { ref } from 'vue'

const name = ref('')
const phone = ref('')
const medicalRecord = ref('')
const location = ref('')
const email = ref('')
const password = ref('')
const isLogin = ref(true)

function toggleForm() {
  isLogin.value = !isLogin.value
}

async function handleAuth() {
  try {
    const endpoint = isLogin.value ? 'login' : 'signup'
    const payload = {
      email: email.value,
      password: password.value,
    }

    if (!isLogin.value) {
      // Add extra signup fields
      payload.name = name.value
      payload.phone = phone.value
      payload.medicalRecord = medicalRecord.value
      payload.location = location.value
    }

    const res = await fetch(`http://localhost:5001/${endpoint}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    })

    const data = await res.json()
    if (!res.ok) throw new Error(data.error || 'Auth failed')

    alert(data.message)
  } catch (err) {
    alert(err.message)
  }
}
</script>
