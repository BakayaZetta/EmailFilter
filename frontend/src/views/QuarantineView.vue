<script setup>
import { ref, onMounted } from 'vue';
import { useAuthStore } from '@/stores/authStore';
import api from '@/services/api';
import { useRouter } from 'vue-router';

const router = useRouter();
const authStore = useAuthStore();
const mails = ref([]);
const loading = ref(true);
const error = ref(null);

// Formater la date pour l'affichage
const formatDate = (dateString) => {
  if (!dateString) return 'N/A';
  return new Date(dateString).toLocaleString();
};

// Obtenir le nom court du statut (pour les classes CSS)
const getStatusClass = (status) => {
  switch(status?.toUpperCase()) {
    case 'QUARANTINE': return 'bg-yellow-100 text-yellow-800';
    case 'ERROR': return 'bg-red-100 text-red-800';
    default: return 'bg-gray-100 text-gray-800';
  }
};

// Charger les mails en quarantaine et avec erreur
const loadQuarantineMails = async () => {
  loading.value = true;
  error.value = null;

  try {
    if (!authStore.isLoggedIn) {
      throw new Error('User must be logged in');
    }

    // Récupérer TOUS les mails en quarantaine et avec erreur (vue administrateur)
    const response = await api.get(`/mails/status/filter`, {
      params: { status: 'QUARANTINE,ERROR' }
    });

    mails.value = response.data;
  } catch (err) {
    console.error('Failed to load quarantine mails:', err);
    error.value = 'Failed to load quarantine mails. Please try again later.';
  } finally {
    loading.value = false;
  }
};

// Marquer un mail comme sûr
const markAsSafe = async (mailId) => {
  try {
    await api.put(`/mails/${mailId}`, { status: 'SAFE' });
    // Recharger la liste après modification
    await loadQuarantineMails();
  } catch (err) {
    console.error('Failed to update mail status:', err);
    alert('Failed to update mail status. Please try again.');
  }
};

// Supprimer un mail
const deleteMail = async (mailId) => {
  if (confirm('Are you sure you want to delete this mail?')) {
    try {
      await api.put(`/mails/${mailId}`, { status: 'DELETED' });
      // Recharger la liste après modification
      await loadQuarantineMails();
    } catch (err) {
      console.error('Failed to delete mail:', err);
      alert('Failed to delete mail. Please try again.');
    }
  }
};

// Vérifier l'authentification et charger les données
onMounted(async () => {
  authStore.initialize();

  if (authStore.isLoggedIn) {
    // Option: Ajouter une vérification du rôle d'administrateur ici si nécessaire
    // if (authStore.user?.role !== 'ADMIN') {
    //   router.push('/');
    //   return;
    // }
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
      <div class="max-w-7xl mx-auto">
        <div class="flex justify-between items-center mb-3">
          <h1 class="text-3xl font-bold">Quarantine - Administrator View</h1>
          <button
            @click="loadQuarantineMails"
            class="text-xs bg-gray-100 hover:bg-gray-200 px-2 py-1 rounded flex items-center"
          >
            <span class="mr-1">⟳</span> Refresh
          </button>
        </div>
        <p class="text-sm text-gray-600 mb-3">All emails detected as potentially malicious or containing errors.</p>

        <div v-if="loading" class="flex justify-center py-6">
          <div class="animate-spin rounded-full h-8 w-8 border-t-2 border-b-2 border-red-500"></div>
        </div>

        <div v-else-if="error" class="bg-red-50 border-l-4 border-red-500 p-2 mb-3 text-sm">
          <p class="text-red-700">{{ error }}</p>
        </div>

        <div v-else-if="mails.length === 0" class="bg-gray-50 rounded-lg p-4 text-center">
          <div class="text-gray-500 text-sm mb-1">No quarantined emails found</div>
          <p class="text-gray-400 text-xs">The system has not detected any suspicious emails</p>
        </div>

        <!-- Wrapper with shadow and rounded corners -->
        <div v-else class="bg-white shadow rounded-lg overflow-hidden">
          <!-- Container for both horizontal and vertical scrolling -->
          <div class="overflow-auto max-h-[70vh]">
            <table class="w-full divide-y divide-gray-200 text-sm">
              <thead class="bg-gray-50 sticky top-0 z-10">
                <tr class="text-xs">
                  <th scope="col" class="px-2 py-2 text-left font-medium text-gray-500 uppercase tracking-wider w-20">Status</th>
                  <th scope="col" class="px-2 py-2 text-left font-medium text-gray-500 uppercase tracking-wider">User</th>
                  <th scope="col" class="px-2 py-2 text-left font-medium text-gray-500 uppercase tracking-wider">Sender</th>
                  <th scope="col" class="px-2 py-2 text-left font-medium text-gray-500 uppercase tracking-wider">Subject</th>
                  <th scope="col" class="px-2 py-2 text-left font-medium text-gray-500 uppercase tracking-wider">Received</th>
                  <th scope="col" class="px-2 py-2 text-left font-medium text-gray-500 uppercase tracking-wider">Actions</th>
                </tr>
              </thead>
              <tbody class="bg-white divide-y divide-gray-200">
                <tr v-for="mail in mails" :key="mail.ID_Mail">
                  <td class="px-4 py-2 whitespace-nowrap">
                    <span :class="['inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium', getStatusClass(mail.Statut)]">
                      {{ mail.Statut }}
                    </span>
                  </td>
                  <td class="px-4 py-2 whitespace-nowrap">
                    User ID: {{ mail.ID_Utilisateur }}
                  </td>
                  <td class="px-4 py-2 whitespace-nowrap">{{ mail.Emetteur }}</td>
                  <td class="px-4 py-2 whitespace-nowrap">{{ mail.Sujet }}</td>
                  <td class="px-4 py-2 whitespace-nowrap">{{ formatDate(mail.Date_Reception) }}</td>
                  <td class="px-4 py-2 whitespace-nowrap">
                    <div class="flex space-x-2">
                      <button @click="markAsSafe(mail.ID_Mail)" class="text-green-600 hover:text-green-900">
                        Mark as Safe
                      </button>
                      <button @click="deleteMail(mail.ID_Mail)" class="text-red-600 hover:text-red-900">
                        Delete
                      </button>
                    </div>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  </section>
</template>
