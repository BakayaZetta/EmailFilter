<script setup>
import { onMounted } from 'vue';
import { useAuthStore } from '@/stores/authStore';
import { useRouter } from 'vue-router';
import { useToast } from 'vue-toastification'; // Import pour toast
import FilterRulesList from '@/components/settings/FilterRulesList.vue';

const router = useRouter();
const authStore = useAuthStore();
const toast = useToast(); // Initialiser toast

// Handler pour les événements du composant enfant
const handleRuleAdded = () => {
  toast.success('Filtering rule added successfully!');
};

const handleRuleUpdated = () => {
  toast.success('Filtering rule updated successfully!');
};

const handleRuleDeleted = () => {
  toast.success('Filtering rule deleted successfully!');
};

const handleRuleError = (errorMessage) => {
  toast.error(errorMessage || 'An error occurred with filtering rules');
};

// Check authentication on mount
onMounted(async () => {
  authStore.initialize();

  if (!authStore.isLoggedIn) {
    // Redirect to login if not connected
    router.push('/login');
  }
});
</script>

<template>
  <section class="py-4">
    <div class="container mx-auto px-2">
      <div class="max-w-5xl mx-auto">
        <!-- Page header -->
        <div class="mb-6">
          <h1 class="text-2xl font-semibold mb-2">Settings</h1>
          <p class="text-sm text-gray-500">
            Configure filtering rules to automatically block unwanted emails.
          </p>
        </div>

        <!-- Email filtering rules section -->
        <div class="mb-8">
          <div class="flex justify-between items-center mb-4">
            <h2 class="text-lg font-semibold">Email Filtering Rules</h2>
          </div>
          <p class="text-sm text-gray-500 mb-4">
            Configure which email senders will be automatically blocked. Emails from these senders won't appear in your inbox.
          </p>

          <FilterRulesList
            @rule-added="handleRuleAdded"
            @rule-updated="handleRuleUpdated"
            @rule-deleted="handleRuleDeleted"
            @rule-error="handleRuleError"
          />
        </div>

        <!-- Help section -->
        <div class="bg-white rounded-lg shadow-md p-6 mb-6">
          <h3 class="text-lg font-semibold mb-3">About Filtering Rules</h3>
          <div class="text-sm text-gray-600 space-y-2">
            <p>
              <strong>How it works:</strong> When an email is received, the system automatically checks if the sender's address matches one of your filtering rules.
            </p>
            <p>
              <strong>Actions:</strong> All emails matching your filtering rules will be automatically blocked and moved to quarantine.
            </p>
            <p>
              <strong>Best practices:</strong> Add email addresses of known spammers or unwanted senders to prevent their messages from reaching your inbox.
            </p>
          </div>
        </div>
      </div>
    </div>
  </section>
</template>
