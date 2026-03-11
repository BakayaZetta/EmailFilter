<script setup>
import { ref, onMounted, watch } from 'vue';
import api from '@/services/api';
import SecurityAnalysisComponent from '@/components/SecurityAnalysisComponent.vue';

// Props pour recevoir le mail à afficher
const props = defineProps({
  mail: {
    type: Object,
    required: true
  },
  expanded: {
    type: Boolean,
    default: false
  }
});

// Émissions pour communiquer avec le composant parent
const emit = defineEmits(['close']);

// État local du composant
const loading = ref(false);
const mailDetails = ref(null);
const showRawHtml = ref(false);

// Fonction pour charger les détails complets du mail
const loadMailDetails = async () => {
  if (!props.mail?.ID_Mail) return;

  loading.value = true;
  try {
    const response = await api.get(`/mails/${props.mail.ID_Mail}/complete`);
    mailDetails.value = response.data;
  } catch (error) {
    console.error('Error loading email details:', error);
  } finally {
    loading.value = false;
  }
};

// Fonction pour fermer le composant
const close = () => {
  emit('close');
};

// Fonction pour empêcher les clics sur le contenu des emails
const preventClicks = (event) => {
  let target = event.target;
  while (target) {
    if (target.tagName && target.tagName.toLowerCase() === 'a') {
      event.preventDefault();
      event.stopPropagation();
      alert('Link clicking is disabled for security reasons. This email may be a phishing attempt.');
      return;
    }
    target = target.parentElement;
  }
};

// Charger les détails du mail si le composant est développé
watch(() => props.expanded, (isExpanded) => {
  if (isExpanded && !mailDetails.value) {
    loadMailDetails();
  }
});

// Initialisation au montage
onMounted(() => {
  if (props.expanded) {
    loadMailDetails();
  }
});
</script>

<template>
  <div class="animate-fadeIn">
    <div class="bg-white rounded-md shadow p-4">
      <div v-if="loading" class="flex justify-center py-10">
        <div class="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-red-500"></div>
        <span class="ml-3 text-red-500">Loading details...</span>
      </div>

      <div v-else-if="!mailDetails" class="bg-red-50 p-4 rounded text-red-700">
        Unable to load email details.
      </div>

      <div v-else>
        <!-- Security analysis component -->
        <div class="mb-4">
          <SecurityAnalysisComponent
            :analyses="mailDetails.analyses"
            :links="mailDetails.links"
            :attachments="mailDetails.attachments"
            :mail-status="mailDetails.status"
          />
        </div>

        <!-- Email header details -->
        <div class="mb-3 border-t border-b py-3">
          <div class="grid grid-cols-2 gap-2 text-sm">
            <div>
              <span class="font-semibold">From:</span> {{ mailDetails.sender }}
            </div>
            <div>
              <span class="font-semibold">To:</span> {{ mailDetails.user?.email || `User ID: ${mailDetails.user?.id}` }}
            </div>
            <div>
              <span class="font-semibold">Subject:</span> {{ mailDetails.subject }}
            </div>
            <div>
              <span class="font-semibold">Date:</span> {{ new Date(mailDetails.receivedDate).toLocaleString() }}
            </div>
          </div>
        </div>

        <!-- Email body -->
        <div class="mb-3">
          <div class="flex justify-between items-center mb-2">
            <h3 class="text-sm font-semibold">Email Content</h3>
            <div class="flex space-x-2">
              <button @click="showRawHtml = !showRawHtml"
                class="text-xs bg-gray-100 hover:bg-gray-200 px-2 py-1 rounded flex items-center"
                :class="{ 'bg-blue-100': showRawHtml }">
                <i class="pi" :class="showRawHtml ? 'pi-code' : 'pi-eye'"></i>
                <span class="ml-1">{{ showRawHtml ? 'Show Rendered' : 'Show Raw HTML' }}</span>
              </button>
              <button @click="close()"
                class="text-xs bg-gray-200 hover:bg-gray-300 text-gray-700 px-2 py-1 rounded flex items-center">
                <i class="pi pi-times mr-1"></i> Close
              </button>
            </div>
          </div>

          <!-- Security indicator -->
          <div class="bg-red-100 text-red-800 px-3 py-1 mb-3 text-sm rounded flex items-center">
            <i class="pi pi-lock mr-1 text-sm"></i>
            <span>Secure View: Links and forms are disabled</span>
          </div>

          <!-- Rendered content (default) -->
          <div v-if="!showRawHtml" class="email-content bg-white p-3 rounded border relative" @click="preventClicks">
            <div v-html="mailDetails.content || '<em>The content of this email is not available or is empty.</em>'"></div>
          </div>

          <!-- Raw content (optional) -->
          <div v-else
            class="whitespace-pre-wrap text-sm bg-gray-50 p-3 rounded border overflow-auto max-h-[400px] font-mono">
            {{ mailDetails.content || "The content of this email is not available or is empty." }}
          </div>

          <!-- Security warning -->
          <div class="text-xs text-amber-600 mt-1 flex items-center">
            <i class="pi pi-exclamation-triangle text-xs mr-1"></i>
            <span>Warning: This email may contain unsafe content</span>
          </div>
        </div>

        <!-- Footer with close button -->
        <div class="mt-3 flex justify-end">
          <button @click="close()"
            class="text-xs bg-gray-200 hover:bg-gray-300 text-gray-700 px-2 py-1 rounded flex items-center">
            <i class="pi pi-times mr-1"></i> Close
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
/* Animation pour l'apparition du contenu développé */
@keyframes fadeIn {
  from {
    opacity: 0;
    transform: translateY(-10px);
  }

  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.animate-fadeIn {
  animation: fadeIn 0.2s ease-out forwards;
}

/* Styles pour le contenu des emails */
.email-content {
  max-height: 500px;
  overflow: auto;
  position: relative;
}

/* Styles de base pour le HTML des emails */
.email-content :deep(table) {
  border-collapse: collapse;
  margin: 0.5rem 0;
}

.email-content :deep(td),
.email-content :deep(th) {
  border: 1px solid #ddd;
  padding: 0.5rem;
}

.email-content :deep(img) {
  max-width: 100%;
  height: auto;
}

.email-content :deep(a) {
  color: #3b82f6;
  text-decoration: underline;
}

/* Styles pour les liens dans le contenu rendu sécurisé */
.email-content :deep(a) {
  color: #3b82f6;
  text-decoration: line-through; /* Barrer les liens pour indiquer qu'ils ne sont pas cliquables */
  cursor: not-allowed;
  pointer-events: all;
  position: relative;
}

/* Ajouter un effet visuel sur survol des liens pour indiquer qu'ils ne sont pas cliquables */
.email-content :deep(a):hover::after {
  content: "⛔ Link disabled";
  position: absolute;
  bottom: 100%;
  left: 0;
  background-color: rgba(0, 0, 0, 0.7);
  color: white;
  padding: 2px 5px;
  border-radius: 3px;
  font-size: 10px;
  white-space: nowrap;
}

/* Désactiver les formulaires et les éléments interactifs */
.email-content :deep(form),
.email-content :deep(button),
.email-content :deep(input),
.email-content :deep(select),
.email-content :deep(textarea) {
  pointer-events: none;
  opacity: 0.7;
  cursor: not-allowed;
}

/* Style pour le conteneur sécurisé */
.secured-email-content {
  position: relative;
}
</style>
