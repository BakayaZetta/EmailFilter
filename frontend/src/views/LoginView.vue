<script setup>
import { reactive } from 'vue'
import { RouterLink, useRouter } from 'vue-router';
import api from '@/services/api'; // Importez le service API
import { useAuthStore } from '@/stores/authStore';
import { useToast } from 'vue-toastification'; // Importez useToast

const router = useRouter();
const authStore = useAuthStore();
const toast = useToast(); // Initialiser le toast

const loginForm = reactive({
  email: '',
  password: '',
  rememberMe: false,
  showPassword: false,
  isLoading: false,
  error: '',
  emailError: '',
  passwordError: ''
});

// Email validation
const validateEmail = () => {
  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/
  if (!loginForm.email) {
    loginForm.emailError = 'Email is required'
    return false
  } else if (!emailRegex.test(loginForm.email)) {
    loginForm.emailError = 'Please enter a valid email address'
    return false
  }
  loginForm.emailError = ''
  return true
}

// Password validation
const validatePassword = () => {
  if (!loginForm.password) {
    loginForm.passwordError = 'Password is required'
    return false
  }
  loginForm.passwordError = ''
  return true
}

// Form submission
const handleSubmit = async () => {
  // Reset errors
  loginForm.error = ''

  // Validate form
  const isEmailValid = validateEmail()
  const isPasswordValid = validatePassword()

  if (!isEmailValid || !isPasswordValid) {
    toast.error("Please correct the errors in the form");
    return;
  }

  try {
    loginForm.isLoading = true

    // Utilisation d'Axios à la place de fetch
    const response = await api.post('/auth/login', {
      email: loginForm.email,
      password: loginForm.password
    });

    // Les données sont directement disponibles dans response.data avec Axios
    const data = response.data;

    // Store token in sessionStorage (au lieu de localStorage)
    authStore.login(data.user, data.token);

    // Afficher un toast de succès
    toast.success("Login successful! Welcome back!");

    // Redirect to /
    router.push('/');

  } catch (error) {
    console.error('Login error:', error);

    // Gestion des erreurs améliorée avec Axios
    const errorMessage = error.response?.data?.message || 'Failed to sign in. Please check your credentials and try again.';
    loginForm.error = errorMessage;

    // Afficher un toast d'erreur
    toast.error(errorMessage);

    // NE PAS rediriger après une erreur
  } finally {
    loginForm.isLoading = false;
  }

  // Retourner false pour être absolument sûr que rien ne provoque une soumission
  return false;
}
</script>

<template>
  <div class="rounded-lg divide-y divide-gray-200  ring-1 ring-gray-200  shadow bg-white max-w-sm mx-auto w-full mt-14">

    <div class="px-4 py-5 sm:p-6">
      <div class="w-full max-w-sm space-y-6">
        <div class="text-center">
          <!-- Lock -->
          <div class="mb-2 pointer-events-none">
            <i class="pi pi-lock flex-shrink-0 text-gray-900 text-3xl"></i>
          </div>
          <!-- Title -->
          <div class="text-2xl text-gray-900  font-bold">Welcome back!</div>
          <div class="text-gray-500  mt-1">
            Don't have an account?
            <RouterLink to="/register" class="font-medium text-red-500 hover:text-red-600">
              Sign up
            </RouterLink>.
          </div>
        </div>
        <div class="gap-y-6 flex flex-col">
          <!-- Form -->
          <form class="space-y-6" @submit.prevent="handleSubmit">

            <!-- General error alert - on peut le garder en plus des toasts -->
            <div v-if="loginForm.error" class="bg-red-50 border-l-4 border-red-500 p-4">
              <div class="flex">
                <div class="flex-shrink-0">
                  <i class="pi pi-times-circle text-red-500"></i>
                </div>
                <div class="ml-3">
                  <p class="text-sm text-red-700">{{ loginForm.error }}</p>
                </div>
              </div>
            </div>

            <!-- Email -->
            <div class="">
              <div class="">
                <div class="flex content-center items-center justify-between text-sm">
                  <label for="email" class="block font-medium text-gray-700">Email address</label>
                </div>
              </div>
              <div class="mt-1 relative">
                <div class="relative">
                  <input id="email" v-model="loginForm.email" name="email" type="email" autocomplete="email" required
                    class="relative block w-full disabled:cursor-not-allowed disabled:opacity-75 focus:outline-none border-0 rounded-md placeholder-gray-400 text-sm px-2.5 py-1.5 shadow-sm bg-white text-gray-900 ring-1 ring-inset ring-gray-300  focus:ring-2 focus:ring-red-500"
                    placeholder="Enter your email" :class="{ 'ring-red-300': loginForm.emailError }" />
                </div>
                <p v-if="loginForm.emailError" class="mt-1 text-sm text-red-600">{{ loginForm.emailError }}</p>
              </div>
            </div>

            <!-- Password -->
            <div class="">
              <div class="">
                <div class="flex content-center items-center justify-between text-sm">
                  <label for="password" class="block font-medium text-gray-700">Password</label>
                </div>
              </div>
              <div class="mt-1 relative">
                <div class="relative">
                  <input id="password" v-model="loginForm.password" :type="loginForm.showPassword ? 'text' : 'password'"
                    name="password" autocomplete="current-password" required
                    class="relative block w-full disabled:cursor-not-allowed disabled:opacity-75 focus:outline-none border-0 rounded-md placeholder-gray-400 text-sm px-2.5 py-1.5 shadow-sm bg-white text-gray-900 ring-1 ring-inset ring-gray-300 focus:ring-2 focus:ring-red-500 pe-9"
                    placeholder="Enter your password" :class="{ 'ring-red-300': loginForm.passwordError }" />
                  <button type="button" @click="loginForm.showPassword = !loginForm.showPassword"
                    class="absolute inset-y-0 right-0 pr-3 flex items-center text-gray-500 focus:outline-none">
                    <i v-if="loginForm.showPassword" class="pi pi-eye hover:text-gray-700"></i>
                    <i v-else class="pi pi-eye-slash hover:text-gray-700"></i>
                  </button>
                </div>
                <p v-if="loginForm.passwordError" class="mt-1 text-sm text-red-600">{{ loginForm.passwordError }}</p>
              </div>
            </div>

            <!-- Button -->
            <button type="submit" :disabled="loginForm.isLoading"
              class="focus:outline-none focus-visible:outline-0 disabled:cursor-not-allowed disabled:opacity-75 aria-disabled:cursor-not-allowed aria-disabled:opacity-75 flex-shrink-0 font-medium rounded-md text-sm gap-x-1.5 px-2.5 py-1.5 shadow-sm text-white bg-gray-900 hover:bg-gray-800 disabled:bg-gray-900 aria-disabled:bg-gray-900 focus-visible:ring-inset focus-visible:ring-2 focus-visible:ring-red-500 w-full flex justify-center items-center">
              <span v-if="loginForm.isLoading" class="absolute left-0 inset-y-0 flex items-center pl-3">
                <i class="pi pi-circle animate-spin text-white"></i>
              </span>
              {{ loginForm.isLoading ? 'Signing in...' : 'Sign in' }}
            </button>
          </form>
        </div>
      </div>
    </div>
  </div>
</template>
