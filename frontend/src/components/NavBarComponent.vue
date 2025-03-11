<script setup>
import detectish from '@/assets/img/detectish.png';
import { RouterLink, useRoute, useRouter } from 'vue-router';
import { onMounted, computed } from 'vue';
import { useAuthStore } from '@/stores/authStore';

const route = useRoute();
const router = useRouter();
const authStore = useAuthStore();

// Links for authenticated users
const authenticatedLinks = [
  { name: 'Home', path: '/' },
  { name: 'Quarantine', path: '/quarantine' },
  { name: 'Statistics', path: '/statistics' },
  { name: 'Settings', path: '/settings' },
];

// Links for non-authenticated users
const guestLinks = [
  { name: 'Login', path: '/login' },
  { name: 'Sign up', path: '/register' },
];

// Computed property to get the appropriate links based on auth status
const navigationLinks = computed(() => {
  return authStore.isLoggedIn ? authenticatedLinks : guestLinks;
});

const isActive = (routePath) => {
  return route.path === routePath;
};

// Logout function
const logout = () => {
  authStore.logout();
  router.push('/');
};

// Initialize auth state
onMounted(() => {
  authStore.initialize();
});
</script>

<template>
  <nav class="bg-white border-b border-gray-100">
    <div class="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
      <div class="flex items-center justify-between h-20">
        <div class="flex flex-1 items-center justify-center md:items-stretch md:justify-start">
          <!-- Logo -->
          <RouterLink to="/" class="flex-shrink-0 flex items-center mr-4">
            <img class="h-10 w-auto rounded-full" :src="detectish" alt="Detectish" />
            <span class="hidden md:block text-black text-2xl font-bold ml-2">Detectish</span>
          </RouterLink>

          <div class="md:ml-auto flex items-center">
            <div class="flex space-x-2">
              <!-- Dynamic navigation links -->
              <RouterLink
                v-for="link in navigationLinks"
                :key="link.name"
                :to="link.path"
                :class="[
                  isActive(link.path) ? 'text-red-500' : 'hover:text-red-700',
                  'text-black', 'px-2', 'py-2', 'rounded-md', 'font-medium'
                ]"
              >
                {{ link.name }}
              </RouterLink>

              <!-- Logout button for authenticated users only -->
              <button
                v-if="authStore.isLoggedIn"
                @click="logout"
                class="text-black hover:text-red-700 px-2 py-2 rounded-md font-medium"
              >
                Logout
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  </nav>
</template>
