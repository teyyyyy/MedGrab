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

        <div class="user-input">
          <div class="input-group" :class="{ 'input-error': errorMessage }">
            <label for="userId">Your ID:</label>
            <input
                type="text"
                id="userId"
                v-model="userId"
                placeholder="Enter your ID"
                required
                autocomplete="off"
                :disabled="isLoading || loginState === 'success'"
                @input="clearError"
            >
            <span v-if="validationMessage" class="validation-message">{{ validationMessage }}</span>
          </div>

          <div v-if="errorMessage" class="error-message" :class="loginState">
            <div class="error-icon">❌</div>
            <p>{{ errorMessage }}</p>
          </div>

          <div v-if="loginState === 'success'" class="success-message">
            <div class="success-icon">✅</div>
            <p>Login successful! Redirecting...</p>
          </div>

          <div class="remember-me">
            <input type="checkbox" id="rememberMe" v-model="rememberMe">
            <label for="rememberMe">Remember me on this device</label>
          </div>

          <button
              type="submit"
              :disabled="!userId || isLoading || loginState === 'success'"
              class="submit-btn"
              :class="{ 'loading': isLoading }"
          >
            <span v-if="!userId">Enter ID to continue</span>
            <span v-else-if="isLoading">
              <div class="spinner"></div>
              Checking...
            </span>
            <span v-else-if="loginState === 'success'">Login Successful</span>
            <span v-else>Login</span>
          </button>
        </div>
      </form>

      <div v-if="networkError" class="network-error">
        <p>📶 Network connection issue detected. Please check your internet connection.</p>
      </div>

      <footer class="login-footer">
        <p>&copy; 2025 MedGrab. All rights reserved.</p>
        <div class="login-state-indicator">
          <span class="state-dot" :class="loginState"></span>
          <span class="state-text">{{ loginStateText }}</span>
        </div>
      </footer>
    </div>
  </main>
</template>

<script>
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'

export default {
  name: 'LoginView',
  setup() {
    const userId = ref('')
    const errorMessage = ref('')
    const validationMessage = ref('')
    const router = useRouter()
    const isLoading = ref(false)
    const loginState = ref('idle') // idle, loading, error, network-error, success
    const networkError = ref(false)
    const loginAttempts = ref(0)
    const rememberMe = ref(false)

    // Check if there's a remembered ID
    const checkSavedId = () => {
      const savedId = localStorage.getItem('rememberedId')
      if (savedId) {
        userId.value = savedId
      }
    }

    // Call it on component mount
    checkSavedId()

    const loginStateText = computed(() => {
      switch (loginState.value) {
        case 'idle': return 'Ready'
        case 'loading': return 'Processing'
        case 'error': return 'Login Failed'
        case 'network-error': return 'Network Error'
        case 'success': return 'Login Successful'
        default: return ''
      }
    })

    const clearError = () => {
      errorMessage.value = ''
      validationMessage.value = ''
      if (loginState.value === 'error' || loginState.value === 'network-error') {
        loginState.value = 'idle'
      }
      networkError.value = false
    }

    const validateUserId = () => {
      // Basic validation - adjust as needed for your ID format
      if (userId.value.length < 3) {
        validationMessage.value = 'ID must be at least 3 characters'
        return false
      }
      validationMessage.value = ''
      return true
    }

    const login = async () => {
      if (!userId.value) return
      if (!validateUserId()) return

      clearError()
      isLoading.value = true
      loginState.value = 'loading'
      loginAttempts.value++

      // If remember me is checked, save the ID
      if (rememberMe.value) {
        localStorage.setItem('rememberedId', userId.value)
      } else {
        localStorage.removeItem('rememberedId')
      }

      try {
        // First, try to check if ID exists as a nurse
        const nurseResult = await checkNurse(userId.value)

        if (nurseResult.success) {
          // User is a nurse
          handleSuccessfulLogin('nurse')
          return
        }

        // If not a nurse, check if ID exists as a patient
        const patientResult = await checkPatient(userId.value)

        if (patientResult.success) {
          // User is a patient
          handleSuccessfulLogin('patient')
          return
        }

        // If we get here, the ID doesn't exist in either system
        handleLoginError('ID not found. Please check and try again.')
      } catch (error) {
        console.error('Login error:', error)

        // Check if it's a network error
        if (!navigator.onLine || error.name === 'TypeError') {
          networkError.value = true
          loginState.value = 'network-error'
          errorMessage.value = 'Network connection failed. Please check your internet connection.'
        } else {
          handleLoginError('Something went wrong. Please try again later.')
        }
      } finally {
        isLoading.value = false
      }
    }

    const handleSuccessfulLogin = (role) => {
      loginState.value = 'success'

      // Store user data
      localStorage.setItem('userRole', role)
      localStorage.setItem('userId', userId.value)

      // Add a small delay for user to see success message
      setTimeout(() => {
        if (role === 'nurse') {
          router.push('/report')
        } else {
          router.push('/bookingcreator')
        }
      }, 1000)
    }

    const handleLoginError = (message) => {
      loginState.value = 'error'
      errorMessage.value = message

      // If too many failed attempts, add a suggestion
      if (loginAttempts.value >= 3) {
        errorMessage.value += ' If you\'re having trouble, please contact support.'
      }
    }

    // Function to check if ID exists as a nurse
    const checkNurse = async (id) => {
      try {
        const response = await fetch(`http://localhost:8000/api/nurses/${id}`)

        if (response.ok) {
          return { success: true, data: await response.json() }
        }

        return { success: false }
      } catch (error) {
        console.error('Nurse check error:', error)
        return { success: false, error }
      }
    }

    // Function to check if ID exists as a patient
    const checkPatient = async (id) => {
      try {
        // Based on the booking.py file, this appears to be the patient API endpoint
        const response = await fetch(`https://personal-eassd2ao.outsystemscloud.com/PatientAPI/rest/v2/GetPatient/${id}`)

        if (response.ok) {
          const data = await response.json()
          // Check that we actually got patient data back
          if (data && data.Patient) {
            return { success: true, data }
          }
        }

        return { success: false }
      } catch (error) {
        console.error('Patient check error:', error)
        return { success: false, error }
      }
    }

    return {
      userId,
      errorMessage,
      validationMessage,
      isLoading,
      loginState,
      loginStateText,
      networkError,
      rememberMe,
      login,
      clearError
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

.input-group.input-error input {
  border-color: #e53935;
}

.validation-message {
  color: #ff9800;
  font-size: 0.85rem;
}

.error-message {
  color: #e53935;
  font-size: 0.9rem;
  font-weight: 500;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.5rem;
  padding: 0.75rem;
  border-radius: 8px;
  background: rgba(229, 57, 53, 0.1);
}

.success-message {
  color: #4caf50;
  font-size: 0.9rem;
  font-weight: 500;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.5rem;
  padding: 0.75rem;
  border-radius: 8px;
  background: rgba(76, 175, 80, 0.1);
}

.remember-me {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-size: 0.9rem;
  color: #555;
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
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.5rem;
}

.submit-btn:hover:not(:disabled) {
  background: #388e3c;
  transform: translateY(-2px);
}

.submit-btn:disabled {
  background: #cccccc;
  cursor: not-allowed;
}

.submit-btn.loading {
  background: #8bc34a;
}

/* Spinner for loading state */
.spinner {
  width: 16px;
  height: 16px;
  border: 3px solid rgba(255, 255, 255, 0.3);
  border-radius: 50%;
  border-top-color: white;
  animation: spin 1s ease-in-out infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

/* Network Error */
.network-error {
  background: #ffecb3;
  padding: 0.75rem;
  border-radius: 8px;
  font-size: 0.9rem;
  text-align: center;
  color: #e65100;
}

/* Footer */
.login-footer {
  text-align: center;
  font-size: 0.9rem;
  color: #777777;
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.login-state-indicator {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.5rem;
  font-size: 0.85rem;
}

.state-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #9e9e9e;
}

.state-dot.idle { background: #9e9e9e; }
.state-dot.loading { background: #2196f3; animation: pulse 1.5s infinite; }
.state-dot.error { background: #e53935; }
.state-dot.network-error { background: #ff9800; }
.state-dot.success { background: #4caf50; }

@keyframes pulse {
  0% { opacity: 1; }
  50% { opacity: 0.4; }
  100% { opacity: 1; }
}

/* Responsive Adjustments */
@media (max-width: 480px) {
  .login-form {
    padding: 1.5rem;
  }
}
</style>