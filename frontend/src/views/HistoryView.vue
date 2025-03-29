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

// Fonctions spécifiques à la vue History
const loadHistoryMails = async () => {
  // Charger les mails avec statut SAFE, DELETED ou PASS
  await loadMails('SAFE,DELETED,PASS');
};

// Actions spécifiques à la vue History
const bulkRestoreToQuarantine = async () => {
  if (selectedMails.value.length === 0) {
    alert('Please select at least one email to restore to quarantine.');
    return;
  }
  await bulkUpdateStatus('QUARANTINE');
};

const restoreToQuarantine = async (mailId) => {
  await updateMailStatus(mailId, 'QUARANTINE');
};

// Vérifier l'authentification et charger les données au montage
onMounted(async () => {
  authStore.initialize();

  if (authStore.isLoggedIn) {
    await loadHistoryMails();
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
          :status-types="['SAFE', 'DELETED', 'PASS']"
          @toggle-select-all="toggleSelectAll"
          @toggle-select="toggleSelect"
          @toggle-expand="toggleExpand"
          @toggle-sort="toggleSort"
          @refresh="loadHistoryMails"
        >
          <!-- Header slot avec titre personnalisé -->
          <template #header>
            <h1 class="text-3xl font-bold">Email History</h1>
          </template>

          <!-- Description slot -->
          <template #description>
            <p class="text-sm text-gray-600 mb-3">
              History of processed emails (safe, deleted, or automatically passed).
            </p>
          </template>

          <!-- Message quand la liste est vide -->
          <template #empty-message>
            No processed emails in the history
          </template>

          <!-- Actions en masse - uniquement déplacement vers quarantaine -->
          <template #bulk-actions="{ selectedCount }">
            <button
              @click="bulkRestoreToQuarantine"
              class="px-3 py-1 bg-yellow-500 text-white text-sm rounded hover:bg-yellow-600 mr-2 disabled:opacity-50"
              :disabled="selectedCount === 0"
            >
              <i class="pi pi-undo mr-1 text-xs"></i> Move to Quarantine
            </button>
          </template>

          <!-- Actions par ligne - uniquement déplacement vers quarantaine -->
          <template #row-actions="{ mail }">
            <button
              v-if="mail.Statut !== 'DELETED'"
              @click="restoreToQuarantine(mail.ID_Mail)"
              title="Move to Quarantine"
              class="px-2 py-1 text-white bg-yellow-500 hover:bg-yellow-600 rounded-full"
            >
              <i class="pi pi-undo text-xs"></i>
            </button>
            <span v-if="mail.Statut === 'DELETED'" class="text-xs text-gray-500">
              Deleted
            </span>
          </template>
        </MailTableComponent>
      </div>
    </div>
  </section>
</template>
