<script setup>
import HeroComponent from '@/components/HeroComponent.vue';
import { onMounted, ref } from 'vue';
import { useAuthStore } from '@/stores/authStore';
import { useToast } from 'vue-toastification'; // Import pour toast
import statisticsService from '@/services/statisticsService';

const authStore = useAuthStore();
const toast = useToast(); // Initialiser toast

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
    console.error('Failed to load statistics:', err);
    toast.error('Unable to load dashboard statistics');
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

</script>

<template>
  <div>
    <!-- Hero component for all users -->
    <HeroComponent />

    <!-- Dashboard for authenticated users - with quick actions only, no welcome message -->
    <section v-if="authStore.isLoggedIn" class="bg-white py-8">
      <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <h2 class="text-xl font-semibold mb-6">Quick Actions</h2>

        <!-- Quick actions -->
        <div class="grid grid-cols-1 md:grid-cols-3 gap-6">
          <router-link to="/quarantine" class="group">
            <div class="bg-white rounded-xl shadow-md hover:shadow-lg transition-shadow p-6 border border-gray-100 group-hover:border-red-100">
              <div class="bg-red-100 rounded-full w-14 h-14 flex items-center justify-center text-red-500 mb-4 group-hover:bg-red-500 group-hover:text-white transition-colors">
                <i class="pi pi-shield text-2xl"></i>
              </div>
              <h3 class="text-lg font-semibold mb-2">Quarantine Management</h3>
              <p class="text-gray-600 text-sm mb-4">Review suspicious emails and take appropriate actions</p>
              <div class="flex items-center text-red-500 group-hover:translate-x-1 transition-transform">
                <span class="text-sm font-medium">Review Quarantine</span>
                <i class="pi pi-arrow-right text-xs ml-1"></i>
              </div>
            </div>
          </router-link>

          <router-link to="/statistics" class="group">
            <div class="bg-white rounded-xl shadow-md hover:shadow-lg transition-shadow p-6 border border-gray-100 group-hover:border-blue-100">
              <div class="bg-blue-100 rounded-full w-14 h-14 flex items-center justify-center text-blue-500 mb-4 group-hover:bg-blue-500 group-hover:text-white transition-colors">
                <i class="pi pi-chart-bar text-2xl"></i>
              </div>
              <h3 class="text-lg font-semibold mb-2">Security Analytics</h3>
              <p class="text-gray-600 text-sm mb-4">View detailed statistics and trends for your emails</p>
              <div class="flex items-center text-blue-500 group-hover:translate-x-1 transition-transform">
                <span class="text-sm font-medium">View Statistics</span>
                <i class="pi pi-arrow-right text-xs ml-1"></i>
              </div>
            </div>
          </router-link>

          <router-link to="/settings" class="group">
            <div class="bg-white rounded-xl shadow-md hover:shadow-lg transition-shadow p-6 border border-gray-100 group-hover:border-purple-100">
              <div class="bg-purple-100 rounded-full w-14 h-14 flex items-center justify-center text-purple-500 mb-4 group-hover:bg-purple-500 group-hover:text-white transition-colors">
                <i class="pi pi-cog text-2xl"></i>
              </div>
              <h3 class="text-lg font-semibold mb-2">Settings</h3>
              <p class="text-gray-600 text-sm mb-4">Manage your account and security preferences</p>
              <div class="flex items-center text-purple-500 group-hover:translate-x-1 transition-transform">
                <span class="text-sm font-medium">Adjust Settings</span>
                <i class="pi pi-arrow-right text-xs ml-1"></i>
              </div>
            </div>
          </router-link>
        </div>
      </div>
    </section>
  </div>
</template>
