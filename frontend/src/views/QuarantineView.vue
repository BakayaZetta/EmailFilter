<script setup>
import { onMounted } from 'vue';
import { useAuthStore } from '@/stores/authStore';
import { useRouter } from 'vue-router';
import { useMailTable } from '@/composables/useMailTable';
import MailTableComponent from '@/components/MailTableComponent.vue';

const router = useRouter();
const authStore = useAuthStore();

// Utiliser le composable useMailTable pour la logique de gestion des mails
const {
  loading,
  error,
  expandedMailId,
  selectedMails,
  sortColumn,
  sortDirection,
  sortedMails,
  loadMails,
  toggleSelectAll,
  toggleSelect,
  toggleExpand,
  toggleSort,
  bulkUpdateStatus,
  updateMailStatus
} = useMailTable();

// Fonctions spécifiques à la vue Quarantine
const loadQuarantineMails = async () => {
  // Charger les mails avec statut QUARANTINE ou ERROR
  await loadMails('QUARANTINE,ERROR');
};

// Actions spécifiques à la vue Quarantine
const bulkMarkAsSafe = async () => {
  if (selectedMails.value.length === 0) {
    alert('Please select at least one email to mark as safe.');
    return;
  }
  await bulkUpdateStatus('SAFE');
};

const bulkDelete = async () => {
  if (selectedMails.value.length === 0) {
    alert('Please select at least one email to delete.');
    return;
  }

  if (confirm(`Are you sure you want to delete ${selectedMails.value.length} email(s)?`)) {
    await bulkUpdateStatus('DELETED');
  }
};

const markAsSafe = async (mailId) => {
  await updateMailStatus(mailId, 'SAFE');
};

const deleteMail = async (mailId) => {
  if (confirm('Are you sure you want to delete this mail?')) {
    await updateMailStatus(mailId, 'DELETED');
  }
};

// Vérifier l'authentification et charger les données au montage
onMounted(async () => {
  authStore.initialize();

  if (authStore.isLoggedIn) {
    await loadQuarantineMails();
  } else {
    // Rediriger vers login si non connecté
    router.push('/login');
  }
});
</script>

<template>
  <section class="py-4">
    <div class="container mx-auto px-2">
      <div class="max-w-full mx-auto">
        <MailTableComponent
          :mails="sortedMails"
          :loading="loading"
          :error="error"
          :expanded-mail-id="expandedMailId"
          :selected-mails="selectedMails"
          :sort-column="sortColumn"
          :sort-direction="sortDirection"
          :status-types="['QUARANTINE', 'ERROR']"
          @toggle-select-all="toggleSelectAll"
          @toggle-select="toggleSelect"
          @toggle-expand="toggleExpand"
          @toggle-sort="toggleSort"
          @refresh="loadQuarantineMails"
        >
          <!-- Header slot avec titre personnalisé -->
          <template #header>
            <h1 class="text-3xl font-bold">Quarantine</h1>
          </template>

          <!-- Description slot -->
          <template #description>
            <p class="text-sm text-gray-600 mb-3">
              All emails detected as potentially malicious or containing errors.
            </p>
          </template>

          <!-- Message quand la liste est vide -->
          <template #empty-message>
            The system has not detected any suspicious emails
          </template>

          <!-- Actions en masse -->
          <template #bulk-actions="{ selectedCount }">
            <button
              @click="bulkMarkAsSafe"
              class="px-3 py-1 bg-green-500 text-white text-sm rounded hover:bg-green-600 mr-2 disabled:opacity-50"
              :disabled="selectedCount === 0"
            >
              <i class="pi pi-check mr-1 text-xs"></i> Mark as Safe
            </button>
            <button
              @click="bulkDelete"
              class="px-3 py-1 bg-red-500 text-white text-sm rounded hover:bg-red-600 disabled:opacity-50"
              :disabled="selectedCount === 0"
            >
              <i class="pi pi-trash mr-1 text-xs"></i> Delete
            </button>
          </template>

          <!-- Actions par ligne -->
          <template #row-actions="{ mail }">
            <button
              @click="markAsSafe(mail.ID_Mail)"
              title="Mark as Safe"
              class="px-2 py-1 text-white bg-green-500 hover:bg-green-600 rounded-full"
            >
              <i class="pi pi-check text-xs"></i>
            </button>
            <button
              @click="deleteMail(mail.ID_Mail)"
              title="Delete"
              class="px-2 py-1 text-white bg-red-500 hover:bg-red-600 rounded-full"
            >
              <i class="pi pi-trash text-xs"></i>
            </button>
          </template>
        </MailTableComponent>
      </div>
    </div>
  </section>
</template>
