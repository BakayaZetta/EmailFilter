<script setup>
import { reactive, onMounted, ref } from 'vue';
import { RouterLink, useRouter } from 'vue-router';
import api from '@/services/api';
import { useAuthStore } from '@/stores/authStore';
import { useToast } from 'vue-toastification';

const router = useRouter();
const authStore = useAuthStore();
const toast = useToast();
const firstNameInput = ref(null);

const registerForm = reactive({
  firstName: '',
  lastName: '',
  email: '',
  password: '',
  confirmPassword: '',
  verificationCode: '',
  showPassword: false,
  isLoading: false,
  isVerifying: false,
  verificationRequested: false,
  error: ''
});

onMounted(() => {
  setTimeout(() => {
    if (firstNameInput.value) {
      firstNameInput.value.focus();
    }
  }, 100);
});

const validateForm = () => {
  if (!registerForm.firstName || !registerForm.lastName || !registerForm.email || !registerForm.password) {
    toast.error('Please fill all required fields');
    return false;
  }

  if (registerForm.password.length < 6) {
    toast.error('Password must be at least 6 characters');
    return false;
  }

  if (registerForm.password !== registerForm.confirmPassword) {
    toast.error('Passwords do not match');
    return false;
  }

  return true;
};

const requestVerification = async () => {
  registerForm.error = '';
  if (!validateForm()) {
    return;
  }

  try {
    registerForm.isLoading = true;
    await api.post('/auth/register/request-verification', {
      firstName: registerForm.firstName,
      lastName: registerForm.lastName,
      email: registerForm.email,
      password: registerForm.password
    });

    registerForm.verificationRequested = true;
    toast.success('Verification code sent to your email');
  } catch (error) {
    registerForm.error = error.response?.data?.message || 'Failed to start registration verification';
    toast.error(registerForm.error);
  } finally {
    registerForm.isLoading = false;
  }
};

const verifyAndCreateAccount = async () => {
  if (!registerForm.verificationCode) {
    toast.error('Verification code is required');
    return;
  }

  try {
    registerForm.isVerifying = true;
    const response = await api.post('/auth/register/verify', {
      email: registerForm.email,
      code: registerForm.verificationCode
    });

    authStore.login(response.data.user, response.data.token);
    toast.success('Account created and verified successfully!');
    router.push('/');
  } catch (error) {
    toast.error(error.response?.data?.message || 'Verification failed');
  } finally {
    registerForm.isVerifying = false;
  }
};

const resendVerification = async () => {
  try {
    await api.post('/auth/verification/resend', {
      email: registerForm.email,
      purpose: 'register'
    });
    toast.success('Verification code resent');
  } catch (error) {
    toast.error(error.response?.data?.message || 'Failed to resend verification code');
  }
};
</script>

<template>
  <div class="rounded-lg divide-y divide-gray-200 ring-1 ring-gray-200 shadow bg-white max-w-sm mx-auto w-full mt-14">
    <div class="px-4 py-5 sm:p-6">
      <div class="w-full max-w-sm space-y-6">
        <div class="text-center">
          <div class="text-2xl text-gray-900 font-bold">Create an account</div>
          <div class="text-gray-500 mt-1">
            Already have an account?
            <RouterLink to="/login" class="font-medium text-red-500 hover:text-red-600">
              Sign in
            </RouterLink>.
          </div>
        </div>

        <form class="space-y-4" @submit.prevent="requestVerification">
          <div v-if="registerForm.error" class="bg-red-50 border-l-4 border-red-500 p-4">
            <p class="text-sm text-red-700">{{ registerForm.error }}</p>
          </div>

          <input ref="firstNameInput" v-model="registerForm.firstName" type="text" placeholder="First name" required class="block w-full rounded-md text-sm px-2.5 py-1.5 shadow-sm ring-1 ring-inset ring-gray-300 focus:ring-2 focus:ring-red-500" />
          <input v-model="registerForm.lastName" type="text" placeholder="Last name" required class="block w-full rounded-md text-sm px-2.5 py-1.5 shadow-sm ring-1 ring-inset ring-gray-300 focus:ring-2 focus:ring-red-500" />
          <input v-model="registerForm.email" type="email" placeholder="Email" required class="block w-full rounded-md text-sm px-2.5 py-1.5 shadow-sm ring-1 ring-inset ring-gray-300 focus:ring-2 focus:ring-red-500" />

          <div class="relative">
            <input
              v-model="registerForm.password"
              :type="registerForm.showPassword ? 'text' : 'password'"
              placeholder="Password"
              required
              class="block w-full rounded-md text-sm px-2.5 py-1.5 shadow-sm ring-1 ring-inset ring-gray-300 focus:ring-2 focus:ring-red-500 pe-9"
            />
            <button type="button" @click="registerForm.showPassword = !registerForm.showPassword" class="absolute inset-y-0 right-0 pr-3 flex items-center text-gray-500">
              <i v-if="registerForm.showPassword" class="pi pi-eye"></i>
              <i v-else class="pi pi-eye-slash"></i>
            </button>
          </div>

          <input v-model="registerForm.confirmPassword" :type="registerForm.showPassword ? 'text' : 'password'" placeholder="Confirm password" required class="block w-full rounded-md text-sm px-2.5 py-1.5 shadow-sm ring-1 ring-inset ring-gray-300 focus:ring-2 focus:ring-red-500" />

          <button type="submit" :disabled="registerForm.isLoading" class="font-medium rounded-md text-sm px-2.5 py-1.5 shadow-sm text-white bg-gray-900 hover:bg-gray-800 w-full">
            {{ registerForm.isLoading ? 'Sending code...' : 'Verify email to create account' }}
          </button>
        </form>

        <div v-if="registerForm.verificationRequested" class="pt-4 border-t border-gray-200 space-y-3">
          <h3 class="text-sm font-semibold text-gray-800">Enter email verification code</h3>
          <input
            v-model="registerForm.verificationCode"
            type="text"
            placeholder="Verification code"
            class="block w-full rounded-md text-sm px-2.5 py-1.5 shadow-sm ring-1 ring-inset ring-gray-300 focus:ring-2 focus:ring-red-500"
          />
          <div class="flex gap-2">
            <button type="button" @click="verifyAndCreateAccount" :disabled="registerForm.isVerifying" class="font-medium rounded-md text-sm px-2.5 py-1.5 shadow-sm text-white bg-gray-900 hover:bg-gray-800">
              {{ registerForm.isVerifying ? 'Creating account...' : 'Create account' }}
            </button>
            <button type="button" @click="resendVerification" class="font-medium rounded-md text-sm px-2.5 py-1.5 border border-gray-300 hover:bg-gray-50">
              Resend code
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
