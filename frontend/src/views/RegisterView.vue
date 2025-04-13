<script setup>
import { reactive, onMounted, ref } from 'vue'
import { RouterLink, useRouter } from 'vue-router';
import api from '@/services/api'; // Importez le service API
import { useAuthStore } from '@/stores/authStore'; // Importez le store d'authentification
import { useToast } from 'vue-toastification'; // Import du service de toast

const router = useRouter();
const authStore = useAuthStore(); // Utilisez le store d'authentification
const toast = useToast(); // Initialisation du toast
const firstNameInput = ref(null); // Référence pour auto-focus

const registerForm = reactive({
  firstName: '',
  lastName: '',
  email: '',
  password: '',
  confirmPassword: '',
  rememberMe: false,
  showPassword: false,
  isLoading: false,
  error: '',
  firstNameError: '',
  lastNameError: '',
  emailError: '',
  passwordError: '',
  confirmPasswordError: ''
});

// Auto-focus sur le champ prénom au chargement
onMounted(() => {
  setTimeout(() => {
    if (firstNameInput.value) {
      firstNameInput.value.focus();
    }
  }, 100);
});

// First name validation
const validateFirstName = () => {
  if (!registerForm.firstName) {
    registerForm.firstNameError = 'First name is required'
    return false
  }
  registerForm.firstNameError = ''
  return true
}

// Last name validation
const validateLastName = () => {
  if (!registerForm.lastName) {
    registerForm.lastNameError = 'Last name is required'
    return false
  }
  registerForm.lastNameError = ''
  return true
}

// Email validation
const validateEmail = () => {
  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/
  if (!registerForm.email) {
    registerForm.emailError = 'Email is required'
    return false
  } else if (!emailRegex.test(registerForm.email)) {
    registerForm.emailError = 'Please enter a valid email address'
    return false
  }
  registerForm.emailError = ''
  return true
}

// Password validation
const validatePassword = () => {
  if (!registerForm.password) {
    registerForm.passwordError = 'Password is required'
    return false
  } else if (registerForm.password.length < 6) {
    registerForm.passwordError = 'Password must be at least 6 characters'
    return false
  }
  registerForm.passwordError = ''
  return true
}

// Confirm password validation
const validateConfirmPassword = () => {
  if (!registerForm.confirmPassword) {
    registerForm.confirmPasswordError = 'Please confirm your password'
    return false
  } else if (registerForm.confirmPassword !== registerForm.password) {
    registerForm.confirmPasswordError = 'Passwords do not match'
    return false
  }
  registerForm.confirmPasswordError = ''
  return true
}

// Validation à la volée quand l'utilisateur quitte un champ
const validateFirstNameOnBlur = () => {
  validateFirstName();
}

const validateLastNameOnBlur = () => {
  validateLastName();
}

const validateEmailOnBlur = () => {
  validateEmail();
}

const validatePasswordOnBlur = () => {
  validatePassword();
  // Valider aussi la confirmation si elle existe déjà
  if (registerForm.confirmPassword) {
    validateConfirmPassword();
  }
}

const validateConfirmPasswordOnBlur = () => {
  validateConfirmPassword();
}

// Gestion de la navigation clavier entre les champs
const handleKeyDown = (event, nextFieldId) => {
  if (event.key === 'Enter') {
    event.preventDefault();
    document.getElementById(nextFieldId).focus();
  }
}

// Form submission
const handleSubmit = async () => {
  // Reset errors
  registerForm.error = ''

  // Validate form
  const isFirstNameValid = validateFirstName()
  const isLastNameValid = validateLastName()
  const isEmailValid = validateEmail()
  const isPasswordValid = validatePassword()
  const isConfirmPasswordValid = validateConfirmPassword()

  if (!isFirstNameValid || !isLastNameValid || !isEmailValid || !isPasswordValid || !isConfirmPasswordValid) {
    toast.error("Please correct the errors in the form"); // Notification d'erreur de validation

    // Mettre le focus sur le premier champ avec erreur
    if (!isFirstNameValid) {
      document.getElementById('firstName').focus();
    } else if (!isLastNameValid) {
      document.getElementById('lastName').focus();
    } else if (!isEmailValid) {
      document.getElementById('email').focus();
    } else if (!isPasswordValid) {
      document.getElementById('password').focus();
    } else {
      document.getElementById('confirmPassword').focus();
    }

    return;
  }

  try {
    registerForm.isLoading = true

    // Utilisation d'Axios à la place de fetch
    const response = await api.post('/auth/register', {
      firstName: registerForm.firstName,
      lastName: registerForm.lastName,
      email: registerForm.email,
      password: registerForm.password
    });

    // Les données sont directement disponibles dans response.data avec Axios
    const data = response.data;

    // Utiliser authStore au lieu de sessionStorage
    authStore.login(data.user, data.token);

    // Notification de succès
    toast.success("Account created successfully! Welcome to Detectish!");

    // Redirect to /
    router.push('/');

  } catch (error) {
    // Gestion des erreurs améliorée avec Axios
    const errorMessage = error.response?.data?.message || 'Failed to create account. Please try again later.';
    registerForm.error = errorMessage;

    // Notification d'erreur
    toast.error(errorMessage);

    console.error('Registration error:', error)

    // Focus sur le premier champ
    document.getElementById('firstName').focus();
  } finally {
    registerForm.isLoading = false
  }

  return false; // Pour s'assurer que la soumission du formulaire est complètement contrôlée
}
</script>

<template>
  <div class="rounded-lg divide-y divide-gray-200  ring-1 ring-gray-200  shadow bg-white max-w-sm mx-auto w-full mt-14">

    <div class="px-4 py-5 sm:p-6">
      <div class="w-full max-w-sm space-y-6">
        <div class="text-center">
          <!-- Title -->
          <div class="text-2xl text-gray-900  font-bold">Create an account</div>
          <div class="text-gray-500  mt-1">
            Already have an account?
            <RouterLink to="/login" class="font-medium text-red-500 hover:text-red-600">
              Sign in
            </RouterLink>.
          </div>
        </div>
        <div class="gap-y-6 flex flex-col">
          <!-- Form -->
          <form class="space-y-6" @submit.prevent="handleSubmit">

            <!-- General error alert -->
            <div v-if="registerForm.error" class="bg-red-50 border-l-4 border-red-500 p-4">
              <div class="flex">
                <div class="flex-shrink-0">
                  <i class="pi pi-times-circle text-red-500"></i>
                </div>
                <div class="ml-3">
                  <p class="text-sm text-red-700">{{ registerForm.error }}</p>
                </div>
              </div>
            </div>

            <!-- First Name -->
            <div class="">
              <div class="">
                <div class="flex content-center items-center justify-between text-sm">
                  <label for="firstName" class="block font-medium text-gray-700">First Name</label>
                </div>
              </div>
              <div class="mt-1 relative">
                <div class="relative">
                  <input id="firstName" ref="firstNameInput" v-model="registerForm.firstName" name="firstName" type="text"
                    autocomplete="given-name" required @blur="validateFirstNameOnBlur"
                    @keydown="(e) => handleKeyDown(e, 'lastName')"
                    class="relative block w-full disabled:cursor-not-allowed disabled:opacity-75 focus:outline-none border-0 rounded-md placeholder-gray-400 text-sm px-2.5 py-1.5 shadow-sm bg-white text-gray-900 ring-1 ring-inset ring-gray-300  focus:ring-2 focus:ring-red-500"
                    placeholder="Enter your first name" :class="{ 'ring-red-300': registerForm.firstNameError }" />
                </div>
                <p v-if="registerForm.firstNameError" class="mt-1 text-sm text-red-600">{{ registerForm.firstNameError
                }}</p>
              </div>
            </div>

            <!-- Last Name -->
            <div class="">
              <div class="">
                <div class="flex content-center items-center justify-between text-sm">
                  <label for="lastName" class="block font-medium text-gray-700">Last Name</label>
                </div>
              </div>
              <div class="mt-1 relative">
                <div class="relative">
                  <input id="lastName" v-model="registerForm.lastName" name="lastName" type="text"
                    autocomplete="family-name" required @blur="validateLastNameOnBlur"
                    @keydown="(e) => handleKeyDown(e, 'email')"
                    class="relative block w-full disabled:cursor-not-allowed disabled:opacity-75 focus:outline-none border-0 rounded-md placeholder-gray-400 text-sm px-2.5 py-1.5 shadow-sm bg-white text-gray-900 ring-1 ring-inset ring-gray-300  focus:ring-2 focus:ring-red-500"
                    placeholder="Enter your last name" :class="{ 'ring-red-300': registerForm.lastNameError }" />
                </div>
                <p v-if="registerForm.lastNameError" class="mt-1 text-sm text-red-600">{{ registerForm.lastNameError }}
                </p>
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
                  <input id="email" v-model="registerForm.email" name="email" type="email" autocomplete="email"
                    required @blur="validateEmailOnBlur" @keydown="(e) => handleKeyDown(e, 'password')"
                    class="relative block w-full disabled:cursor-not-allowed disabled:opacity-75 focus:outline-none border-0 rounded-md placeholder-gray-400 text-sm px-2.5 py-1.5 shadow-sm bg-white text-gray-900 ring-1 ring-inset ring-gray-300  focus:ring-2 focus:ring-red-500"
                    placeholder="Enter your email address" :class="{ 'ring-red-300': registerForm.emailError }" />
                </div>
                <p v-if="registerForm.emailError" class="mt-1 text-sm text-red-600">{{ registerForm.emailError }}</p>
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
                  <input id="password" v-model="registerForm.password"
                    :type="registerForm.showPassword ? 'text' : 'password'" name="password" autocomplete="new-password"
                    required @blur="validatePasswordOnBlur" @keydown="(e) => handleKeyDown(e, 'confirmPassword')"
                    class="relative block w-full disabled:cursor-not-allowed disabled:opacity-75 focus:outline-none border-0 rounded-md placeholder-gray-400 text-sm px-2.5 py-1.5 shadow-sm bg-white text-gray-900 ring-1 ring-inset ring-gray-300 focus:ring-2 focus:ring-red-500 pe-9"
                    placeholder="Enter your password" :class="{ 'ring-red-300': registerForm.passwordError }" />
                  <button type="button" @click="registerForm.showPassword = !registerForm.showPassword"
                    class="absolute inset-y-0 right-0 pr-3 flex items-center text-gray-500 focus:outline-none">
                    <i v-if="registerForm.showPassword" class="pi pi-eye hover:text-gray-700"></i>
                    <i v-else class="pi pi-eye-slash hover:text-gray-700"></i>
                  </button>
                </div>
                <p v-if="registerForm.passwordError" class="mt-1 text-sm text-red-600">{{ registerForm.passwordError }}
                </p>
              </div>
            </div>

            <!-- Confirm Password -->
            <div class="">
              <div class="">
                <div class="flex content-center items-center justify-between text-sm">
                  <label for="confirmPassword" class="block font-medium text-gray-700">Confirm Password</label>
                </div>
              </div>
              <div class="mt-1 relative">
                <div class="relative">
                  <input id="confirmPassword" v-model="registerForm.confirmPassword"
                    :type="registerForm.showPassword ? 'text' : 'password'" name="confirmPassword"
                    autocomplete="new-password" required @blur="validateConfirmPasswordOnBlur"
                    class="relative block w-full disabled:cursor-not-allowed disabled:opacity-75 focus:outline-none border-0 rounded-md placeholder-gray-400 text-sm px-2.5 py-1.5 shadow-sm bg-white text-gray-900 ring-1 ring-inset ring-gray-300 focus:ring-2 focus:ring-red-500 pe-9"
                    placeholder="Confirm your password"
                    :class="{ 'ring-red-300': registerForm.confirmPasswordError }" />
                  <button type="button" @click="registerForm.showPassword = !registerForm.showPassword"
                    class="absolute inset-y-0 right-0 pr-3 flex items-center text-gray-500 focus:outline-none">
                    <i v-if="registerForm.showPassword" class="pi pi-eye hover:text-gray-700"></i>
                    <i v-else class="pi pi-eye-slash hover:text-gray-700"></i>
                  </button>
                </div>
                <p v-if="registerForm.confirmPasswordError" class="mt-1 text-sm text-red-600">{{
                  registerForm.confirmPasswordError }}</p>
              </div>
            </div>

            <!-- Button -->
            <button type="submit" :disabled="registerForm.isLoading"
              class="focus:outline-none focus-visible:outline-0 disabled:cursor-not-allowed disabled:opacity-75 aria-disabled:cursor-not-allowed aria-disabled:opacity-75 flex-shrink-0 font-medium rounded-md text-sm gap-x-1.5 px-2.5 py-1.5 shadow-sm text-white bg-gray-900 hover:bg-gray-800 disabled:bg-gray-900 aria-disabled:bg-gray-900 focus-visible:ring-inset focus-visible:ring-2 focus-visible:ring-red-500 w-full flex justify-center items-center">
              <span v-if="registerForm.isLoading" class="absolute left-0 inset-y-0 flex items-center pl-3">
                <i class="pi pi-circle animate-spin text-white"></i>
              </span>
              {{ registerForm.isLoading ? 'Creating account...' : 'Create account' }}
            </button>
          </form>
        </div>
      </div>
    </div>
  </div>
</template>
