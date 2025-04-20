<script setup>
import { computed, ref, onMounted } from 'vue';
import { useRouter } from 'vue-router';
import { useAuthStore } from '@/stores/authStore';
import statisticsService from '@/services/statisticsService';

const router = useRouter();
const authStore = useAuthStore();

// Check if user is authenticated
const isAuthenticated = computed(() => authStore.isLoggedIn);

// Key features of the application
const features = [
  {
    title: "Email Analysis",
    description: "Automatically scan emails for phishing and security threats",
    icon: "pi-shield",
    color: "bg-red-500"
  },
  {
    title: "Quarantine Management",
    description: "Review and handle suspicious emails safely",
    icon: "pi-exclamation-circle",
    color: "bg-yellow-500"
  },
  {
    title: "AI-Powered Insights",
    description: "Get detailed explanations of threats with Mistral AI",
    icon: "pi-comment",
    color: "bg-purple-500"
  },
  {
    title: "Security Analytics",
    description: "Track and analyze email security metrics",
    icon: "pi-chart-line",
    color: "bg-blue-500"
  }
];

// Navigate to primary action based on authentication status
const navigateToPrimaryAction = () => {
  if (isAuthenticated.value) {
    router.push('/quarantine');
  } else {
    router.push('/login');
  }
};

// Navigate to secondary action based on authentication status
const navigateToSecondaryAction = () => {
  if (isAuthenticated.value) {
    router.push('/statistics');
  } else {
    router.push('/register');
  }
};

// Stats for authenticated users
const stats = ref(null);
const statsLoading = ref(false);

// Only show features for non-authenticated users
const showFeatures = computed(() => !isAuthenticated.value);

// Fetch basic stats if authenticated
onMounted(async () => {
  if (isAuthenticated.value) {
    statsLoading.value = true;
    try {
      stats.value = await statisticsService.getStatistics('month');
    } catch (err) {
      console.error('Failed to load stats for hero:', err);
    } finally {
      statsLoading.value = false;
    }
  }
});
</script>

<template>
  <section class="bg-gradient-to-b from-gray-50 to-white">
    <!-- Main hero section -->
    <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 pt-12 pb-8">
      <!-- Hero content -->
      <div class="flex flex-col md:flex-row items-center justify-between gap-12">
        <!-- Left column with text content -->
        <div class="md:w-1/2">
          <!-- For non-authenticated users -->
          <div v-if="!isAuthenticated" class="mb-6">
            <span class="inline-block bg-red-100 text-red-700 px-3 py-1 rounded-full text-sm font-semibold mb-4">
              Security Platform
            </span>
            <h1 class="text-4xl lg:text-5xl font-extrabold text-gray-900 mb-4 leading-tight">
              Protect Your Inbox with <span class="text-red-600">Detectish</span>
            </h1>
            <p class="text-lg text-gray-600 mb-8 max-w-xl">
              Comprehensive email security solution to detect, analyze, and protect against phishing attacks and malicious content.
            </p>
          </div>

          <!-- For authenticated users -->
          <div v-else class="mb-6">
            <h1 class="text-3xl font-bold text-gray-900 mb-2">
              Welcome back, {{ authStore.user?.firstName }}!
            </h1>
            <p class="text-lg text-gray-600 mb-6">
              Your email security at a glance
            </p>

            <!-- Mini stats row (for authenticated users) -->
            <div v-if="stats" class="grid grid-cols-3 gap-3 mb-6">
              <div class="bg-white p-3 rounded-lg shadow-sm border border-gray-100">
                <div class="flex items-center mb-1">
                  <div class="w-6 h-6 rounded-full bg-yellow-100 flex items-center justify-center text-yellow-500 mr-2">
                    <i class="pi pi-exclamation-circle text-xs"></i>
                  </div>
                  <span class="text-xs text-gray-600">Quarantine</span>
                </div>
                <p class="text-lg font-bold">{{ stats.mailsByStatus?.QUARANTINE || 0 }}</p>
              </div>

              <div class="bg-white p-3 rounded-lg shadow-sm border border-gray-100">
                <div class="flex items-center mb-1">
                  <div class="w-6 h-6 rounded-full bg-red-100 flex items-center justify-center text-red-500 mr-2">
                    <i class="pi pi-times-circle text-xs"></i>
                  </div>
                  <span class="text-xs text-gray-600">Errors</span>
                </div>
                <p class="text-lg font-bold">{{ stats.mailsByStatus?.ERROR || 0 }}</p>
              </div>

              <div class="bg-white p-3 rounded-lg shadow-sm border border-gray-100">
                <div class="flex items-center mb-1">
                  <div class="w-6 h-6 rounded-full bg-green-100 flex items-center justify-center text-green-500 mr-2">
                    <i class="pi pi-check-circle text-xs"></i>
                  </div>
                  <span class="text-xs text-gray-600">Safe</span>
                </div>
                <p class="text-lg font-bold">{{ stats.mailsByStatus?.SAFE || 0 }}</p>
              </div>
            </div>

            <div v-else-if="statsLoading" class="flex items-center mb-6">
              <div class="w-4 h-4 border-t-2 border-b-2 border-red-500 rounded-full animate-spin mr-2"></div>
              <span class="text-sm text-gray-500">Loading statistics...</span>
            </div>
          </div>

          <!-- CTA buttons -->
          <div class="flex flex-wrap gap-4">
            <button @click="navigateToPrimaryAction"
              class="px-6 py-3 bg-red-600 text-white font-medium rounded-lg shadow-md hover:bg-red-700 transition-colors flex items-center">
              <i :class="`pi ${isAuthenticated ? 'pi-shield' : 'pi-sign-in'} mr-2`"></i>
              {{ isAuthenticated ? 'View Quarantine' : 'Sign In' }}
            </button>
            <button @click="navigateToSecondaryAction"
              class="px-6 py-3 bg-white text-gray-800 font-medium rounded-lg shadow-md border border-gray-200 hover:bg-gray-50 transition-colors flex items-center">
              <i :class="`pi ${isAuthenticated ? 'pi-chart-bar' : 'pi-user-plus'} mr-2`"></i>
              {{ isAuthenticated ? 'View Statistics' : 'Create Account' }}
            </button>
          </div>
        </div>

        <!-- Right column with illustration -->
        <div class="md:w-1/2 flex justify-center">
          <div class="relative w-full max-w-md">
            <!-- Decorative elements -->
            <div class="absolute -z-10 w-40 h-40 bg-red-100 rounded-full -top-5 -right-10 opacity-60"></div>
            <div class="absolute -z-10 w-32 h-32 bg-yellow-100 rounded-full bottom-10 -left-10 opacity-60"></div>

            <!-- Email security illustration -->
            <div class="bg-white p-6 rounded-xl shadow-lg border border-gray-100 relative z-10">
              <div class="flex items-center justify-between border-b border-gray-100 pb-4 mb-4">
                <div class="flex items-center">
                  <div class="w-8 h-8 rounded-full bg-red-500 flex items-center justify-center text-white">
                    <i class="pi pi-shield"></i>
                  </div>
                  <span class="ml-3 font-semibold">Email Security Alert</span>
                </div>
                <span class="text-xs bg-yellow-100 text-yellow-800 px-2 py-1 rounded-full">Suspicious</span>
              </div>

              <div class="space-y-3">
                <div class="flex space-x-3">
                  <div class="w-6 text-gray-400"><i class="pi pi-user"></i></div>
                  <div class="text-sm">From: <span class="font-medium">security@examp1e.com</span></div>
                </div>
                <div class="flex space-x-3">
                  <div class="w-6 text-gray-400"><i class="pi pi-at"></i></div>
                  <div class="text-sm">To: <span class="font-medium">user@company.com</span></div>
                </div>
                <div class="flex space-x-3">
                  <div class="w-6 text-gray-400"><i class="pi pi-info-circle"></i></div>
                  <div class="text-sm">Subject: <span class="font-medium">Urgent: Verify Your Account</span></div>
                </div>

                <div class="bg-red-50 p-3 rounded-lg border-l-4 border-red-500 mt-4">
                  <div class="flex">
                    <div class="text-red-500 mr-2"><i class="pi pi-exclamation-triangle"></i></div>
                    <div>
                      <p class="text-sm text-red-800 font-semibold">Phishing Attempt Detected</p>
                      <p class="text-xs text-red-700 mt-1">This email contains suspicious links and domain spoofing.</p>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Features section - only show for non-authenticated users -->
      <div v-if="showFeatures" class="mt-24">
        <h2 class="text-2xl font-bold text-center mb-12">Email Security Made Simple</h2>

        <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-8">
          <div v-for="(feature, index) in features" :key="index" class="bg-white p-6 rounded-lg shadow-sm border border-gray-100 hover:shadow-md transition-shadow">
            <div :class="`w-12 h-12 rounded-lg ${feature.color} text-white flex items-center justify-center mb-4`">
              <i :class="`pi ${feature.icon} text-xl`"></i>
            </div>
            <h3 class="text-lg font-semibold mb-2">{{ feature.title }}</h3>
            <p class="text-gray-600 text-sm">{{ feature.description }}</p>
          </div>
        </div>
      </div>
    </div>

    <!-- Bottom wave decoration -->
    <div class="w-full h-24 overflow-hidden">
      <svg viewBox="0 0 1200 120" preserveAspectRatio="none" class="w-full h-full">
        <path
          d="M0,0V46.29c47.79,22.2,103.59,32.17,158,28,70.36-5.37,136.33-33.31,206.8-37.5C438.64,32.43,512.34,53.67,583,72.05c69.27,18,138.3,24.88,209.4,13.08,36.15-6,69.85-17.84,104.45-29.34C989.49,25,1113-14.29,1200,52.47V0Z"
          class="fill-current text-gray-50"
        />
      </svg>
    </div>
  </section>
</template>

<style scoped>
/* Optional animations */
@keyframes float {
  0% { transform: translateY(0px); }
  50% { transform: translateY(-10px); }
  100% { transform: translateY(0px); }
}

.animate-float {
  animation: float 5s ease-in-out infinite;
}
</style>
