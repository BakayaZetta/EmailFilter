<script setup>
import HeroComponent from '@/components/HeroComponent.vue';
import { onMounted, ref } from 'vue';
import { useAuthStore } from '@/stores/authStore';
import { useRouter } from 'vue-router';
import statisticsService from '@/services/statisticsService';

const authStore = useAuthStore();
const router = useRouter();

// État pour les statistiques
const stats = ref(null);
const loading = ref(false);

// Charger les statistiques de base
const loadBasicStats = async () => {
  if (!authStore.isLoggedIn) return;

  loading.value = true;
  try {
    stats.value = await statisticsService.getStatistics('month');
  } catch (err) {
    console.error('Failed to load basic statistics:', err);
  } finally {
    loading.value = false;
  }
};

// Charger les statistiques au montage du composant
onMounted(() => {
  loadBasicStats();
  // Initialize authentication state from sessionStorage
  authStore.initialize();
});

// Logout function if needed locally in the component
const logout = () => {
  authStore.logout();
  router.push('/');
};
</script>

<template>
  <HeroComponent />

  <!-- Authentication Information Section -->
  <section v-if="authStore.isLoggedIn" class="py-8 bg-gray-100">
    <div class="container mx-auto px-4">
      <div class="max-w-3xl mx-auto bg-white rounded-lg shadow p-6">
        <h2 class="text-2xl font-bold mb-6">Authentication Status</h2>

        <div class="space-y-6">
          <div class="bg-green-100 border border-green-200 text-green-700 px-4 py-3 rounded">
            <p class="font-semibold">✓ You are logged in!</p>
          </div>

          <div class="space-y-4">
            <h3 class="text-xl font-semibold">User Information</h3>
            <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <p class="text-sm text-gray-500">Name</p>
                <p class="font-medium">{{ authStore.user.firstName }} {{ authStore.user.lastName }}</p>
              </div>
              <div>
                <p class="text-sm text-gray-500">Email</p>
                <p class="font-medium">{{ authStore.user.email }}</p>
              </div>
              <div>
                <p class="text-sm text-gray-500">User ID</p>
                <p class="font-medium">{{ authStore.user.id }}</p>
              </div>
            </div>
          </div>

          <div class="space-y-2">
            <h3 class="text-xl font-semibold">Authentication Token</h3>
            <div class="bg-gray-50 p-3 rounded border overflow-x-auto">
              <code class="text-sm break-all">{{ authStore.token }}</code>
            </div>
            <p class="text-xs text-gray-500">This is your JWT token used for authentication.</p>
          </div>

          <div class="pt-4 border-t">
            <button @click="logout"
                    class="px-4 py-2 bg-red-600 hover:bg-red-700 text-white rounded transition-colors">
              Sign Out
            </button>
          </div>
        </div>
      </div>
    </div>
  </section>

  <!-- Ajouter cette section après le HeroComponent -->
  <section v-if="authStore.isLoggedIn" class="py-8">
    <div class="container mx-auto px-4">
      <div class="max-w-4xl mx-auto">
        <h2 class="text-2xl font-bold mb-4">Email Security Overview</h2>

        <div v-if="loading" class="flex justify-center py-8">
          <div class="animate-spin rounded-full h-10 w-10 border-b-2 border-blue-700"></div>
        </div>

        <div v-else-if="stats" class="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 gap-4 mb-6">
          <div class="bg-white p-4 rounded-lg shadow-sm border-l-4 border-blue-500">
            <p class="text-sm text-gray-500">Total Emails</p>
            <p class="text-2xl font-bold">{{ stats.totalMails }}</p>
          </div>

          <div class="bg-white p-4 rounded-lg shadow-sm border-l-4 border-yellow-500">
            <p class="text-sm text-gray-500">In Quarantine</p>
            <p class="text-2xl font-bold">{{ stats.mailsByStatus?.QUARANTINE || 0 }}</p>
          </div>

          <div class="bg-white p-4 rounded-lg shadow-sm border-l-4 border-red-500">
            <p class="text-sm text-gray-500">Errors</p>
            <p class="text-2xl font-bold">{{ stats.mailsByStatus?.ERROR || 0 }}</p>
          </div>

          <div class="bg-white p-4 rounded-lg shadow-sm border-l-4 border-green-500">
            <p class="text-sm text-gray-500">Safe</p>
            <p class="text-2xl font-bold">{{ stats.mailsByStatus?.SAFE || 0 }}</p>
          </div>
        </div>

        <div class="text-center">
          <RouterLink
            to="/statistics"
            class="inline-flex items-center px-4 py-2 bg-blue-600 border border-transparent rounded-md font-semibold text-xs text-white uppercase tracking-widest hover:bg-blue-500 active:bg-blue-700 focus:outline-none focus:border-blue-700 focus:ring ring-blue-300 disabled:opacity-25 transition ease-in-out duration-150"
          >
            View Full Statistics <i class="pi pi-arrow-right ml-2"></i>
          </RouterLink>
        </div>
      </div>
    </div>
  </section>
</template>
