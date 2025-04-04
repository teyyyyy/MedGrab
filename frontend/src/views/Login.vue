<template>
    <div class="login-container">
      <h1>Welcome to MedGrab</h1>
      <div class="login-form">
        <div class="role-selection">
          <button 
            @click="setRole('patient')" 
            :class="{ active: role === 'patient' }"
          >
            I'm a Patient
          </button>
          <button 
            @click="setRole('nurse')" 
            :class="{ active: role === 'nurse' }"
          >
            I'm a Nurse
          </button>
        </div>
  
        <div v-if="role" class="user-input">
          <label for="userId">Your {{ role }} ID:</label>
          <input 
            type="text" 
            id="userId" 
            v-model="userId" 
            :placeholder="`Enter your ${role} ID`"
          >
          <button @click="login" :disabled="!userId">Continue</button>
        </div>
      </div>
    </div>
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
  .login-container {
    max-width: 500px;
    margin: 2rem auto;
    padding: 2rem;
    text-align: center;
  }
  
  .login-form {
    background: white;
    padding: 2rem;
    border-radius: 8px;
    box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
  }
  
  .role-selection {
    display: flex;
    gap: 1rem;
    margin-bottom: 2rem;
    justify-content: center;
  }
  
  .role-selection button {
    padding: 0.75rem 1.5rem;
    border: 2px solid #e0e0e0;
    background: white;
    border-radius: 4px;
    cursor: pointer;
    font-weight: 600;
    transition: all 0.2s;
  }
  
  .role-selection button.active {
    background: #1976d2;
    color: white;
    border-color: #1976d2;
  }
  
  .user-input {
    display: flex;
    flex-direction: column;
    gap: 1rem;
  }
  
  .user-input label {
    text-align: left;
    font-weight: 600;
  }
  
  .user-input input {
    padding: 0.75rem;
    border: 1px solid #e0e0e0;
    border-radius: 4px;
    font-size: 1rem;
  }
  
  .user-input button {
    padding: 0.75rem;
    background: #4caf50;
    color: white;
    border: none;
    border-radius: 4px;
    font-weight: 600;
    cursor: pointer;
    transition: background 0.2s;
  }
  
  .user-input button:disabled {
    background: #cccccc;
    cursor: not-allowed;
  }
  
  .user-input button:hover:not(:disabled) {
    background: #388e3c;
  }
  </style>