<script setup>
import { computed, defineProps, defineEmits } from 'vue';
import { marked } from 'marked';

const props = defineProps({
  response: {
    type: String,
    default: null
  },
  loading: {
    type: Boolean,
    default: false
  },
  error: {
    type: String,
    default: null
  },
  emailId: {
    type: [Number, String],
    default: null
  }
});

const emit = defineEmits(['close']);

// Convertir le markdown en HTML
const formattedResponse = computed(() => {
  if (!props.response) return '';
  try {
    return marked.parse(props.response);
  } catch (e) {
    console.error('Error parsing markdown:', e);
    return props.response;
  }
});
</script>

<template>
  <div class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
    <div class="bg-white rounded-lg shadow-xl w-full max-w-2xl animate-scale-in">
      <!-- En-tête -->
      <div class="px-6 py-4 border-b border-gray-200 flex justify-between items-center">
        <h3 class="text-lg font-semibold text-gray-900 flex items-center">
          <i class="pi pi-comment-dots text-purple-500 mr-2"></i>
          Explication Mistral
        </h3>
        <button @click="emit('close')" class="text-gray-400 hover:text-gray-500">
          <i class="pi pi-times"></i>
        </button>
      </div>

      <!-- Contenu -->
      <div class="p-6 overflow-y-auto max-h-[60vh]">
        <!-- Chargement -->
        <div v-if="loading" class="flex flex-col items-center py-10">
          <div class="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-purple-500"></div>
          <p class="mt-3 text-gray-600">Génération de l'explication en cours...</p>
          <p class="text-sm text-gray-500 mt-1">Cela peut prendre quelques secondes</p>
        </div>

        <!-- Erreur -->
        <div v-else-if="error" class="bg-red-50 border-l-4 border-red-500 p-4 rounded">
          <div class="flex">
            <i class="pi pi-exclamation-circle text-red-500 mr-3 mt-0.5"></i>
            <div>
              <h3 class="text-red-800 font-medium">Une erreur est survenue</h3>
              <p class="text-red-700 mt-1">{{ error }}</p>
            </div>
          </div>
        </div>

        <!-- Réponse -->
        <div v-else-if="response" class="prose max-w-none">
          <div class="mb-4 rounded-md">
            <div v-html="formattedResponse" class="text-gray-800"></div>
          </div>
        </div>

        <!-- Pas de réponse -->
        <div v-else class="text-center py-6 text-gray-500">
          Aucune explication disponible
        </div>
      </div>

      <!-- Pied de modal -->
      <div class="px-6 py-4 border-t border-gray-200 flex justify-end">
        <button
          @click="emit('close')"
          class="px-4 py-2 bg-gray-100 hover:bg-gray-200 rounded text-gray-800"
        >
          Fermer
        </button>
      </div>
    </div>
  </div>
</template>

<style scoped>
@keyframes scale-in {
  from {
    opacity: 0;
    transform: scale(0.95);
  }
  to {
    opacity: 1;
    transform: scale(1);
  }
}

.animate-scale-in {
  animation: scale-in 0.2s ease-out forwards;
}

/* Style pour le contenu HTML généré */
:deep(h1) {
  font-size: 1.5rem;
  font-weight: 600;
  margin-top: 0;
  margin-bottom: 1rem;
  color: #4338ca;
}

:deep(h2) {
  font-size: 1.25rem;
  font-weight: 600;
  margin-top: 1.5rem;
  margin-bottom: 0.75rem;
  color: #5b21b6;
}

:deep(h3) {
  font-size: 1.125rem;
  font-weight: 500;
  margin-top: 1.25rem;
  margin-bottom: 0.5rem;
}

:deep(p) {
  margin-bottom: 0.75rem;
  line-height: 1.5;
}

:deep(ul), :deep(ol) {
  margin-left: 1.5rem;
  margin-bottom: 0.75rem;
}

:deep(li) {
  margin-bottom: 0.25rem;
}

:deep(strong), :deep(b) {
  font-weight: 600;
  color: #4c1d95;
}

:deep(code) {
  background-color: #f1f5f9;
  padding: 0.1em 0.25em;
  border-radius: 0.25rem;
  font-family: monospace;
}

:deep(pre) {
  background-color: #f1f5f9;
  padding: 0.5rem;
  border-radius: 0.25rem;
  overflow-x: auto;
}
</style>
