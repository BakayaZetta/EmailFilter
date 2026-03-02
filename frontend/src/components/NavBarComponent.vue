<script setup>
import bakayaTechLogo from '@/assets/img/bakaya_tech.png';
import { RouterLink, useRoute, useRouter } from 'vue-router';
import { onMounted, computed } from 'vue';
import { useAuthStore } from '@/stores/authStore';
import { useToast } from 'vue-toastification'; // Import pour toast

const route = useRoute();
const router = useRouter();
const authStore = useAuthStore();
const toast = useToast(); // Initialiser toast

// Links for authenticated users
const authenticatedLinks = [
  { name: 'Home', path: '/' },
  { name: 'Quarantine', path: '/quarantine' },
  { name: 'History', path: '/history' },
  { name: 'Statistics', path: '/statistics' },
  { name: 'Settings', path: '/settings' },
];

const adminOnlyLinks = [
  { name: 'Admin Portal', path: '/admin' },
];

// Links for non-authenticated users
const guestLinks = [
  { name: 'Login', path: '/login' },
  { name: 'Sign up', path: '/register' },
];

// Computed property to get the appropriate links based on auth status
const navigationLinks = computed(() => {
  if (!authStore.isLoggedIn) {
    return guestLinks;
  }

  const role = String(authStore.user?.role || '').toLowerCase();
  const isAdmin = role === 'admin' || role === 'super_admin' || role === 'superadmin';

  return isAdmin ? [...authenticatedLinks, ...adminOnlyLinks] : authenticatedLinks;
});

const isActive = (routePath) => {
  return route.path === routePath;
};

// Logout function
const logout = () => {
  authStore.logout();
  toast.success('You have been logged out successfully'); // Notification de déconnexion
  router.push('/');
};

// Initialize auth state
onMounted(() => {
  authStore.initialize();
});
</script>

<template>
  <header class="bg-white/65 backdrop-blur border-b border-gray-200 sticky top-0 z-50">

    <nav class="">
      <div class="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
        <div class="flex items-center justify-between h-20">
          <div class="flex flex-1 items-center justify-center md:items-stretch md:justify-start">
            <!-- Logo -->
            <RouterLink to="/" class="flex-shrink-0 flex items-center mr-4">
              <img class="h-10 w-auto rounded-full" :src="bakayaTechLogo" alt="Bakaya Tech" />
              <span class="hidden md:block text-black text-2xl font-bold ml-2">Bakaya Tech</span>
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
  </header>
</template>
