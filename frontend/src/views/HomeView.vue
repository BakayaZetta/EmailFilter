<script setup>
import HeroComponent from '@/components/HeroComponent.vue';
import { onMounted } from 'vue';
import { useAuthStore } from '@/stores/authStore';
import { useRouter } from 'vue-router';

const authStore = useAuthStore();
const router = useRouter();

onMounted(() => {
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
</template>
