<script setup>
import { reactive, onMounted, ref } from 'vue';
import { RouterLink, useRouter } from 'vue-router';
import api from '@/services/api';
import { useAuthStore } from '@/stores/authStore';
import { useToast } from 'vue-toastification';

const router = useRouter();
const authStore = useAuthStore();
const toast = useToast();
const emailInput = ref(null);

const loginForm = reactive({
  email: '',
  password: '',
  rememberMe: false,
  captchaToken: '',
  verificationCode: '',
  showPassword: false,
  isLoading: false,
  isVerifyingCode: false,
  error: '',
  emailError: '',
  passwordError: '',
  requiresCaptcha: false,
  requiresEmailVerification: false
});

onMounted(() => {
  setTimeout(() => {
    if (emailInput.value) {
      emailInput.value.focus();
    }
  }, 100);
});

const validateEmail = () => {
  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  if (!loginForm.email) {
    loginForm.emailError = 'Email is required';
    return false;
  }
  if (!emailRegex.test(loginForm.email)) {
    loginForm.emailError = 'Please enter a valid email address';
    return false;
  }
  loginForm.emailError = '';
  return true;
};

const validatePassword = () => {
  if (!loginForm.password) {
    loginForm.passwordError = 'Password is required';
    return false;
  }
  loginForm.passwordError = '';
  return true;
};

const handleSubmit = async () => {
  loginForm.error = '';

  if (!validateEmail() || !validatePassword()) {
    toast.error('Please correct the errors in the form');
    return;
  }

  try {
    loginForm.isLoading = true;

    const response = await api.post('/auth/login', {
      email: loginForm.email,
      password: loginForm.password,
      captchaToken: loginForm.requiresCaptcha ? loginForm.captchaToken : undefined
    });

    const data = response.data;

    if (data.requiresEmailVerification) {
      loginForm.requiresEmailVerification = true;
      toast.info('Verification code sent to your email.');
      return;
    }

    authStore.login(data.user, data.token);
    toast.success('Login successful! Welcome back!');
    router.push('/');
  } catch (error) {
    const errorMessage = error.response?.data?.message || 'Failed to sign in. Please try again.';
    loginForm.error = errorMessage;

    if (error.response?.data?.requiresCaptcha) {
      loginForm.requiresCaptcha = true;
      toast.warning('Suspicious login detected. Please complete CAPTCHA token validation.');
    } else {
      toast.error(errorMessage);
    }
  } finally {
    loginForm.isLoading = false;
  }
};

const handleVerifyCode = async () => {
  if (!loginForm.verificationCode) {
    toast.error('Verification code is required');
    return;
  }

  try {
    loginForm.isVerifyingCode = true;
    const response = await api.post('/auth/login/verify', {
      email: loginForm.email,
      code: loginForm.verificationCode,
      rememberMe: loginForm.rememberMe
    });

    authStore.login(response.data.user, response.data.token);
    toast.success('Login verified successfully!');
    router.push('/');
  } catch (error) {
    toast.error(error.response?.data?.message || 'Failed to verify login code');
  } finally {
    loginForm.isVerifyingCode = false;
  }
};

const handleResend = async () => {
  try {
    await api.post('/auth/verification/resend', {
      email: loginForm.email,
      purpose: 'login'
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
          <div class="mb-2 pointer-events-none">
            <i class="pi pi-lock flex-shrink-0 text-gray-900 text-3xl"></i>
          </div>
          <div class="text-2xl text-gray-900 font-bold">Welcome back!</div>
          <div class="text-gray-500 mt-1">
            Don't have an account?
            <RouterLink to="/register" class="font-medium text-red-500 hover:text-red-600">
              Sign up
            </RouterLink>.
          </div>
        </div>

        <form class="space-y-6" @submit.prevent="handleSubmit">
          <div v-if="loginForm.error" class="bg-red-50 border-l-4 border-red-500 p-4">
            <p class="text-sm text-red-700">{{ loginForm.error }}</p>
          </div>

          <div>
            <label for="email" class="block font-medium text-gray-700">Email address</label>
            <input
              id="email"
              ref="emailInput"
              v-model="loginForm.email"
              type="email"
              autocomplete="email"
              required
              @blur="validateEmail"
              class="mt-1 block w-full rounded-md text-sm px-2.5 py-1.5 shadow-sm bg-white text-gray-900 ring-1 ring-inset ring-gray-300 focus:ring-2 focus:ring-red-500"
            />
            <p v-if="loginForm.emailError" class="mt-1 text-sm text-red-600">{{ loginForm.emailError }}</p>
          </div>

          <div>
            <label for="password" class="block font-medium text-gray-700">Password</label>
            <div class="mt-1 relative">
              <input
                id="password"
                v-model="loginForm.password"
                :type="loginForm.showPassword ? 'text' : 'password'"
                autocomplete="current-password"
                required
                @blur="validatePassword"
                class="block w-full rounded-md text-sm px-2.5 py-1.5 shadow-sm bg-white text-gray-900 ring-1 ring-inset ring-gray-300 focus:ring-2 focus:ring-red-500 pe-9"
              />
              <button
                type="button"
                @click="loginForm.showPassword = !loginForm.showPassword"
                class="absolute inset-y-0 right-0 pr-3 flex items-center text-gray-500"
              >
                <i v-if="loginForm.showPassword" class="pi pi-eye"></i>
                <i v-else class="pi pi-eye-slash"></i>
              </button>
            </div>
            <p v-if="loginForm.passwordError" class="mt-1 text-sm text-red-600">{{ loginForm.passwordError }}</p>
          </div>

          <div class="flex items-center justify-between text-sm">
            <label class="inline-flex items-center gap-2 text-gray-700">
              <input v-model="loginForm.rememberMe" type="checkbox" class="rounded border-gray-300" />
              Remember me (skip frequent email verification)
            </label>
          </div>

          <div v-if="loginForm.requiresCaptcha">
            <label for="captchaToken" class="block font-medium text-gray-700">CAPTCHA token</label>
            <input
              id="captchaToken"
              v-model="loginForm.captchaToken"
              type="text"
              class="mt-1 block w-full rounded-md text-sm px-2.5 py-1.5 shadow-sm bg-white text-gray-900 ring-1 ring-inset ring-gray-300 focus:ring-2 focus:ring-red-500"
              placeholder="Enter CAPTCHA token"
            />
            <p class="text-xs text-gray-500 mt-1">In development you can use <strong>dev-bypass</strong>.</p>
          </div>

          <button
            type="submit"
            :disabled="loginForm.isLoading"
            class="font-medium rounded-md text-sm px-2.5 py-1.5 shadow-sm text-white bg-gray-900 hover:bg-gray-800 w-full"
          >
            {{ loginForm.isLoading ? 'Signing in...' : 'Sign in' }}
          </button>
        </form>

        <div v-if="loginForm.requiresEmailVerification" class="pt-4 border-t border-gray-200 space-y-3">
          <h3 class="text-sm font-semibold text-gray-800">Email verification required</h3>
          <input
            v-model="loginForm.verificationCode"
            type="text"
            placeholder="Enter verification code"
            class="block w-full rounded-md text-sm px-2.5 py-1.5 shadow-sm bg-white text-gray-900 ring-1 ring-inset ring-gray-300 focus:ring-2 focus:ring-red-500"
          />
          <div class="flex gap-2">
            <button
              type="button"
              @click="handleVerifyCode"
              :disabled="loginForm.isVerifyingCode"
              class="font-medium rounded-md text-sm px-2.5 py-1.5 shadow-sm text-white bg-gray-900 hover:bg-gray-800"
            >
              {{ loginForm.isVerifyingCode ? 'Verifying...' : 'Verify & Login' }}
            </button>
            <button
              type="button"
              @click="handleResend"
              class="font-medium rounded-md text-sm px-2.5 py-1.5 border border-gray-300 hover:bg-gray-50"
            >
              Resend code
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
