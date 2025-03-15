<script setup>
import { ref, onMounted, computed, watch } from 'vue';
import api from '@/services/api';

// Props pour recevoir l'ID du mail à afficher
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
const analyses = ref([]);
const showRawHtml = ref(false);

// Fonction pour charger les analyses du mail
const loadAnalyses = async () => {
  if (!props.mail?.ID_Mail) return;

  loading.value = true;
  try {
    const response = await api.get(`/analysis/mail/${props.mail.ID_Mail}`);
    analyses.value = response.data || [];
  } catch (error) {
    console.error('Erreur lors du chargement des analyses:', error);
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

// Catégoriser les analyses par type
const categorizedAnalyses = computed(() => {
  const result = {
    SPF: analyses.value.filter(a => a.Type_Analyse === 'SPF'),
    DKIM: analyses.value.filter(a => a.Type_Analyse === 'DKIM'),
    DMARC: analyses.value.filter(a => a.Type_Analyse === 'DMARC'),
    AI: analyses.value.filter(a => a.Type_Analyse === 'AI')
  };
  return result;
});

// Obtenir une icône et une couleur basées sur le résultat de l'analyse
const getAnalysisIndicator = (analysis) => {
  const result = analysis.Resultat_Analyse.toLowerCase();

  if (result.includes('valid') || result.includes('pass')) {
    return { icon: 'pi-check-circle', color: 'text-green-500' };
  } else if (result.includes('invalid') || result.includes('fail')) {
    return { icon: 'pi-times-circle', color: 'text-red-500' };
  } else if (result.includes('warning') || result.includes('soft')) {
    return { icon: 'pi-exclamation-triangle', color: 'text-yellow-500' };
  } else {
    return { icon: 'pi-info-circle', color: 'text-gray-500' };
  }
};

// Charger les analyses si le composant est développé
watch(() => props.expanded, (isExpanded) => {
  if (isExpanded && analyses.value.length === 0) {
    loadAnalyses();
  }
});

// Initialisation au montage
onMounted(() => {
  if (props.expanded) {
    loadAnalyses();
  }
});
</script>

<template>
  <div class="animate-fadeIn">
    <div class="bg-white rounded-md shadow p-4">
      <!-- Section des résultats d'analyse -->
      <div class="mb-4">
        <h3 class="text-lg font-semibold mb-2">Analyses de sécurité</h3>

        <div v-if="loading" class="text-center py-2">
          <div class="inline-block animate-spin rounded-full h-4 w-4 border-t-2 border-b-2 border-blue-500"></div>
          <span class="ml-2 text-sm text-gray-600">Chargement des analyses...</span>
        </div>

        <div v-else-if="analyses.length === 0" class="text-sm text-gray-500 italic">
          Aucune analyse disponible pour ce message
        </div>

        <div v-else class="grid grid-cols-1 md:grid-cols-2 gap-3">
          <!-- Résultats SPF -->
          <div v-if="categorizedAnalyses.SPF.length > 0" class="bg-gray-50 p-2 rounded border">
            <div class="flex items-center mb-1">
              <i class="pi pi-shield mr-2 text-blue-600"></i>
              <span class="font-semibold">SPF</span>
            </div>
            <div v-for="analysis in categorizedAnalyses.SPF" :key="analysis.ID_Analyse" class="text-sm">
              <div class="flex items-start">
                <i :class="['pi mr-1', getAnalysisIndicator(analysis).icon, getAnalysisIndicator(analysis).color]"></i>
                <span>{{ analysis.Resultat_Analyse.replace('SPF: ', '') }}</span>
              </div>
            </div>
          </div>

          <!-- Résultats DKIM -->
          <div v-if="categorizedAnalyses.DKIM.length > 0" class="bg-gray-50 p-2 rounded border">
            <div class="flex items-center mb-1">
              <i class="pi pi-key mr-2 text-blue-600"></i>
              <span class="font-semibold">DKIM</span>
            </div>
            <div v-for="analysis in categorizedAnalyses.DKIM" :key="analysis.ID_Analyse" class="text-sm">
              <div class="flex items-start">
                <i :class="['pi mr-1', getAnalysisIndicator(analysis).icon, getAnalysisIndicator(analysis).color]"></i>
                <span>{{ analysis.Resultat_Analyse.replace('DKIM: ', '') }}</span>
              </div>
            </div>
          </div>

          <!-- Résultats DMARC -->
          <div v-if="categorizedAnalyses.DMARC.length > 0" class="bg-gray-50 p-2 rounded border">
            <div class="flex items-center mb-1">
              <i class="pi pi-verified mr-2 text-blue-600"></i>
              <span class="font-semibold">DMARC</span>
            </div>
            <div v-for="analysis in categorizedAnalyses.DMARC" :key="analysis.ID_Analyse" class="text-sm">
              <div class="flex items-start">
                <i :class="['pi mr-1', getAnalysisIndicator(analysis).icon, getAnalysisIndicator(analysis).color]"></i>
                <span>{{ analysis.Resultat_Analyse.replace('DMARC: ', '') }}</span>
              </div>
            </div>
          </div>

          <!-- Résultats AI -->
          <div v-if="categorizedAnalyses.AI.length > 0" class="bg-gray-50 p-2 rounded border">
            <div class="flex items-center mb-1">
              <i class="pi pi-bolt mr-2 text-blue-600"></i>
              <span class="font-semibold">Intelligence Artificielle</span>
            </div>
            <div v-for="analysis in categorizedAnalyses.AI" :key="analysis.ID_Analyse" class="text-sm">
              <div class="flex items-start">
                <span>{{ analysis.Resultat_Analyse.replace('AI_PHISHING: ', '') }}</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- En-tête détaillé du mail -->
      <div class="mb-3 border-t border-b py-3">
        <div class="grid grid-cols-2 gap-2 text-sm">
          <div>
            <span class="font-semibold">From:</span> {{ props.mail.Emetteur }}
          </div>
          <div>
            <span class="font-semibold">Date:</span> {{ new Date(props.mail.Date_Reception).toLocaleString() }}
          </div>
          <div>
            <span class="font-semibold">Subject:</span> {{ props.mail.Sujet }}
          </div>
          <div>
            <span class="font-semibold">Status:</span> {{ props.mail.Statut }}
          </div>
        </div>
      </div>

      <!-- Corps du mail -->
      <div class="mb-3">
        <div class="flex justify-between items-center mb-2">
          <h3 class="text-sm font-semibold">Email Content</h3>
          <div class="flex space-x-2">
            <button
              @click="showRawHtml = !showRawHtml"
              class="text-xs bg-gray-100 hover:bg-gray-200 px-2 py-1 rounded flex items-center"
              :class="{'bg-blue-100': showRawHtml}"
            >
              <i class="pi" :class="showRawHtml ? 'pi-code' : 'pi-eye'"></i>
              <span class="ml-1">{{ showRawHtml ? 'Show Rendered' : 'Show Raw HTML' }}</span>
            </button>
            <button
              @click="close"
              class="text-xs bg-gray-200 hover:bg-gray-300 text-gray-700 px-2 py-1 rounded flex items-center"
            >
              <i class="pi pi-times mr-1"></i> Close
            </button>
          </div>
        </div>

        <!-- Indicateur de sécurité -->
        <div class="bg-red-100 text-red-800 px-3 py-1 mb-3 text-sm rounded flex items-center">
          <i class="pi pi-lock mr-1 text-sm"></i>
          <span>Secure View: Links and forms are disabled</span>
        </div>

        <!-- Contenu interprété (par défaut) -->
        <div
          v-if="!showRawHtml"
          class="email-content bg-white p-3 rounded border relative"
          @click="preventClicks"
        >
          <div v-html="props.mail.Contenu || '<em>The content of this email is not available or is empty.</em>'"></div>
        </div>

        <!-- Contenu brut (option) -->
        <div v-else class="whitespace-pre-wrap text-sm bg-gray-50 p-3 rounded border overflow-auto max-h-[400px] font-mono">
          {{ props.mail.Contenu || "The content of this email is not available or is empty." }}
        </div>

        <!-- Avertissement de sécurité -->
        <div class="text-xs text-amber-600 mt-1 flex items-center">
          <i class="pi pi-exclamation-triangle text-xs mr-1"></i>
          <span>Warning: This email may contain unsafe content</span>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
/* Animation pour l'apparition du contenu développé */
@keyframes fadeIn {
  from { opacity: 0; transform: translateY(-10px); }
  to { opacity: 1; transform: translateY(0); }
}

.animate-fadeIn {
  animation: fadeIn 0.2s ease-out forwards;
}

/* Styles pour le contenu des emails */
.email-content {
  max-height: 500px;
  overflow: auto;
  position: relative; /* Pour le positionnement des éléments enfants */
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
