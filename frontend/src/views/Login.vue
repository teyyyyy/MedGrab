<template>
  <main class="login-page">
    <div class="login-container">
      <header class="login-header">
        <div class="logo">
          <span class="logo-icon">💊</span>
          <h1>MedGrab</h1>
        </div>
        <p class="tagline">Care Arriving.</p>
      </header>

      <form class="login-form" @submit.prevent="login">
        <h2>Log in to continue</h2>

        <fieldset class="role-selection">
          <legend class="visually-hidden">Select your role</legend>
          <button
              type="button"
              @click="setRole('patient')"
              :class="['role-btn', { active: role === 'patient' }]"
              aria-pressed="role === 'patient'"
          >
            <span class="icon">👤</span>
            <span>I'm a Patient</span>
          </button>

          <button
              type="button"
              @click="setRole('nurse')"
              :class="['role-btn', { active: role === 'nurse' }]"
              aria-pressed="role === 'nurse'"
          >
            <span class="icon">👩‍⚕️</span>
            <span>I'm a Nurse</span>
          </button>
        </fieldset>

        <transition name="fade">
          <div v-if="role" class="user-input">
            <div class="input-group">
              <label for="userId">Your {{ role }} ID:</label>
              <input
                  type="text"
                  id="userId"
                  v-model="userId"
                  :placeholder="`Enter your ${role} ID`"
                  required
                  autocomplete="off"
              >
            </div>

            <button
                type="submit"
                :disabled="!userId"
                class="submit-btn"
            >
              <span v-if="!userId">Enter ID to continue</span>
              <span v-else>Continue to Dashboard</span>
            </button>
          </div>
        </transition>
      </form>

      <footer class="login-footer">
        <p>&copy; 2025 MedGrab. All rights reserved.</p>
      </footer>
    </div>
  </main>
</template>

<script>
import { ref } from 'vue'
import { useRouter } from 'vue-router'

export default {
  name: 'LoginView',
  setup() {
    const role = ref('')
    const userId = ref('')
    const router = useRouter()

    const setRole = (selectedRole) => {
      role.value = selectedRole
    }

    const login = () => {
      if (!role.value || !userId.value) return

      // Store user info in localStorage
      localStorage.setItem('userRole', role.value)
      localStorage.setItem('userId', userId.value)

      // Redirect based on role
      if (role.value === 'patient') {
        router.push('/bookingcreator')
      } else {
        router.push('/report')
      }
    }

    return {
      role,
      userId,
      setRole,
      login
    }
  }
}
</script>

<style scoped>
/* Global styles - no fancy variables since they're actin' dodgy */

/* Layout & Container */
.login-page {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #f5f7fa;
  padding: 1rem;
}

.login-container {
  width: 100%;
  max-width: 480px;
  display: flex;
  flex-direction: column;
  gap: 2rem;
}

/* Header & Branding */
.login-header {
  text-align: center;
  margin-bottom: 1rem;
}

.logo {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.5rem;
  margin-bottom: 0.5rem;
}

.logo-icon {
  font-size: 2rem;
}

.login-header h1 {
  font-size: 2.2rem;
  font-weight: 700;
  color: #2D87D3;
  margin: 0;
}

.tagline {
  font-size: 1.1rem;
  color: #777777;
  margin: 0;
}

/* Form Elements */
.login-form {
  background: white;
  padding: 2rem;
  border-radius: 12px;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.1);
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
}

.login-form h2 {
  margin: 0 0 1rem;
  font-size: 1.4rem;
  color: #333333;
  text-align: center;
}

.role-selection {
  display: flex;
  gap: 1rem;
  margin-bottom: 1rem;
  border: none;
  padding: 0;
}

.visually-hidden {
  position: absolute;
  width: 1px;
  height: 1px;
  padding: 0;
  margin: -1px;
  overflow: hidden;
  clip: rect(0, 0, 0, 0);
  white-space: nowrap;
  border-width: 0;
}

.role-btn {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.5rem;
  padding: 1rem;
  border: 2px solid #e0e0e0;
  background: white;
  border-radius: 8px;
  cursor: pointer;
  font-weight: 600;
  transition: all 0.3s ease;
}

.role-btn .icon {
  font-size: 1.8rem;
  margin-bottom: 0.5rem;
}

.role-btn:hover {
  border-color: #2D87D3;
  transform: translateY(-2px);
}

.role-btn.active {
  background: #2D87D3;
  color: white;
  border-color: #2D87D3;
  transform: translateY(-2px);
  box-shadow: 0 4px 8px rgba(29, 118, 210, 0.2);
}

.user-input {
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
}

.input-group {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.input-group label {
  font-weight: 600;
  font-size: 0.95rem;
  color: #333333;
}

.input-group input {
  padding: 0.9rem;
  border: 2px solid #e0e0e0;
  border-radius: 8px;
  font-size: 1rem;
  transition: all 0.3s ease;
}

.input-group input:focus {
  border-color: #2D87D3;
  outline: none;
  box-shadow: 0 0 0 3px rgba(29, 118, 210, 0.1);
}

.submit-btn {
  padding: 0.9rem;
  background: #4caf50;
  color: white;
  border: none;
  border-radius: 8px;
  font-weight: 600;
  font-size: 1rem;
  cursor: pointer;
  transition: all 0.3s ease;
}

.submit-btn:hover:not(:disabled) {
  background: #388e3c;
  transform: translateY(-2px);
}

.submit-btn:disabled {
  background: #cccccc;
  cursor: not-allowed;
}

/* Footer */
.login-footer {
  text-align: center;
  font-size: 0.9rem;
  color: #777777;
}

/* Animations */
.fade-enter-active, .fade-leave-active {
  transition: opacity 0.3s ease, transform 0.3s ease;
}

.fade-enter-from, .fade-leave-to {
  opacity: 0;
  transform: translateY(10px);
}

/* Responsive Adjustments */
@media (max-width: 480px) {
  .login-form {
    padding: 1.5rem;
  }

  .role-selection {
    flex-direction: column;
  }

  .role-btn {
    flex-direction: row;
    justify-content: center;
  }

  .role-btn .icon {
    margin-bottom: 0;
    margin-right: 0.5rem;
  }
}
</style>